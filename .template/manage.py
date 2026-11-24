#!/usr/bin/env python3
"""Preview or conservatively apply agent-repo-template files; Python stdlib only."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

SCHEMA = 'agent-repo-template/v1'
STATE = '.agents/template-state.json'
BEGIN = '<!-- agent-repo-template:begin -->'
END = '<!-- agent-repo-template:end -->'
CORE = {'AGENTS.md'}
LEGACY_INDEX = '.agents/README.md'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    p = PurePosixPath(relative)
    if not isinstance(relative, str) or not relative or p.is_absolute() or '..' in p.parts or str(p) != relative or '\\' in relative:
        raise ValueError(f'unsafe relative path: {relative}')
    out = root
    for part in p.parts:
        out = out / part
        if out.is_symlink():
            raise ValueError(f'symlink not supported: {out}')
        if out.exists() and out != root / relative and not out.is_dir():
            raise ValueError(f'parent is not a directory: {out}')
    if out.exists() and not out.is_file():
        raise ValueError(f'not a regular file: {out}')
    return out


def allowed_target(path, legacy=False):
    return (legacy and path == LEGACY_INDEX) or path in CORE or bool(re.fullmatch(r'\.agents/(policies|runbooks)/[a-z0-9-]+\.(md|yaml)', path))


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def block(data):
    text = data.decode('utf-8')
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise ValueError('invalid AGENTS.md managed markers')
    if BEGIN not in text:
        return None
    start, end = text.index(BEGIN), text.index(END) + len(END)
    if text.index(END) < start:
        raise ValueError('reversed AGENTS.md managed markers')
    return text[start:end].encode()


def replace_block(current, wanted):
    existing = block(current)
    if existing is None:
        return current + (b'\n\n' if current else b'') + wanted + b'\n'
    return current.replace(existing, wanted, 1)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).strip()


def plan(source, target, modules):
    manifest_path = safe_path(source, '.template/manifest.json')
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get('schema') != SCHEMA or not isinstance(manifest.get('version'), str) or manifest.get('source') != 'jay1803/agent-repo-template':
        raise ValueError('unsupported template manifest')
    revision = git(source, 'rev-parse', 'HEAD').decode()
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('source must have an immutable Git commit')
    rows = manifest['files']
    if not isinstance(rows, list):
        raise ValueError('manifest files must be a list')
    seen = set()
    for row in rows:
        if set(row) != {'source', 'target', 'module'} or not all(isinstance(x, str) for x in row.values()):
            raise ValueError('invalid manifest file entry')
        if not allowed_target(row['target']) or row['target'] in seen:
            raise ValueError(f'unsupported or duplicate target: {row["target"]}')
        if not re.fullmatch('[a-z][a-z0-9-]*', row['module']):
            raise ValueError('invalid module name')
        seen.add(row['target'])
        safe_path(source, row['source'])
        safe_path(target, row['target'])
    if not CORE.issubset({r['target'] for r in rows if r['module'] == 'core'}):
        raise ValueError('missing core files')
    # Bind all inputs, including the executable, to the same reviewed revision.
    for relative in {'.template/manifest.json', '.template/manage.py', *(r['source'] for r in rows)}:
        actual = safe_path(source, relative).read_bytes()
        committed = subprocess.check_output(['git', '-C', str(source), 'show', f'{revision}:{relative}'], stderr=subprocess.PIPE)
        if committed != actual:
            raise ValueError(f'source differs from commit: {relative}')
    state_path = safe_path(target, STATE)
    state = read_json(state_path) if state_path.exists() else {'schema': SCHEMA, 'source': manifest['source'], 'files': {}}
    if not isinstance(state, dict) or state.get('schema') != SCHEMA or state.get('source') != manifest['source'] or not isinstance(state.get('files'), dict):
        raise ValueError('invalid or foreign template state')
    records = state['files']
    for path, record in records.items():
        if not allowed_target(path, legacy=True) or not isinstance(record, dict) or set(record) != {'sha256', 'revision', 'module'}:
            raise ValueError('invalid state file entry')
        if not re.fullmatch('[0-9a-f]{64}', record['sha256']) or not re.fullmatch('[0-9a-f]{40}', record['revision']) or not isinstance(record['module'], str):
            raise ValueError('invalid state fingerprint')
        safe_path(target, path)
    available = {r['module'] for r in rows}
    if set(modules) - available:
        raise ValueError(f'unknown modules: {sorted(set(modules) - available)}')
    selected = {'core', *modules, *(r['module'] for r in records.values())}
    actions, writes = [], {}
    new_records = dict(records)
    for row in rows:
        if row['module'] not in selected:
            continue
        path = row['target']
        dest = safe_path(target, path)
        current = dest.read_bytes() if dest.exists() else None
        desired = safe_path(source, row['source']).read_bytes()
        if path == 'AGENTS.md':
            desired = block(desired)
            if desired is None:
                raise ValueError('template AGENTS.md lacks managed block')
            comparable = block(current) if current is not None else None
        else:
            comparable = current
        old = records.get(path)
        if comparable == desired:
            status = 'unchanged'
        elif old and comparable is None:
            status = 'preserve-deleted'
        elif old and digest(comparable) != old['sha256']:
            status = 'preserve-local'
        elif path == 'AGENTS.md' and LEGACY_INDEX in records and safe_path(target, LEGACY_INDEX).exists():
            status = 'index-migration-required'
        elif old and path.startswith('.agents/policies/'):
            status = 'policy-review-required'
        elif current is not None and not old and (path != 'AGENTS.md' or comparable is not None):
            status = 'preserve-existing'
        else:
            status = 'update' if old else ('append' if current is not None else 'create')
            writes[path] = replace_block(current or b'', desired) if path == 'AGENTS.md' else desired
        if status in {'unchanged', 'create', 'append', 'update'}:
            new_records[path] = {'sha256': digest(desired), 'revision': revision, 'module': row['module']}
        actions.append({'path': path, 'status': status})
    for path in records.keys() - seen:
        # Forget the retired index only after an explicit migration removed it
        # and the root no longer refers to it. Never delete user content here.
        root_file = safe_path(target, 'AGENTS.md')
        root_content = writes.get('AGENTS.md', root_file.read_bytes() if root_file.exists() else b'')
        if path == LEGACY_INDEX and not safe_path(target, path).exists() and LEGACY_INDEX.encode() not in root_content:
            new_records.pop(path)
            actions.append({'path': path, 'status': 'retired-removed'})
        else:
            actions.append({'path': path, 'status': 'preserve-retired'})
    new_state = {'schema': SCHEMA, 'source': manifest['source'], 'files': new_records}
    encoded = (json.dumps(new_state, indent=2, sort_keys=True) + '\n').encode()
    if not state_path.exists() or state_path.read_bytes() != encoded:
        writes[STATE] = encoded
    before = {p: safe_path(target, p).read_bytes() if safe_path(target, p).exists() else None for p in writes}
    return {'source': manifest['source'], 'revision': revision, 'version': manifest['version'], 'actions': actions}, writes, before


def apply(target, writes, before):
    # Check the entire write set first; fail before writes if another process changed it.
    for relative, expected in before.items():
        path = safe_path(target, relative)
        actual = path.read_bytes() if path.exists() else None
        if actual != expected:
            raise ValueError(f'target changed after planning: {relative}')
    # No deletes, chmod, Git operations, network calls, or arbitrary template paths.
    for relative, data in writes.items():
        path = safe_path(target, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        if before[relative] is None:
            with path.open('xb') as handle:
                handle.write(data)
        else:
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.agent-template-', delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(data)
                temporary.chmod(path.stat().st_mode & 0o777)
                os.replace(temporary, path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True, type=Path)
    parser.add_argument('--modules', nargs='*', default=[], help='optional modules to add; recorded modules remain selected')
    parser.add_argument('--apply', action='store_true', help='write the safe subset; default only prints the plan')
    args = parser.parse_args()
    try:
        target = Path(os.path.abspath(args.target))
        if not target.is_dir() or target.resolve() != target:
            raise ValueError('target must be an existing directory without symlink components; use its physical path')
        result, writes, before = plan(Path(__file__).resolve().parent.parent, target, args.modules)
        if args.apply:
            apply(target, writes, before)
        result['applied'] = args.apply
        result['write_paths'] = sorted(writes)
        result['needs_attention'] = any(x['status'].startswith('preserve-') or x['status'] in {'policy-review-required', 'index-migration-required'} for x in result['actions'])
        print(json.dumps(result, indent=2))
        return 2 if result['needs_attention'] else 0
    except (ValueError, TypeError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
