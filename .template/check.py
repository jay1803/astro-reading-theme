#!/usr/bin/env python3
"""Validate the bundled inventory and release-policy/v1 example without dependencies."""
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('manage', root / '.template/manage.py')
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)
manifest = manage.read_json(root / '.template/manifest.json')
assert manifest['schema'] == manage.SCHEMA
assert manifest['source'] == 'jay1803/agent-repo-template'
assert manage.block((root / 'AGENTS.md').read_bytes())
expected = {
    'core': {'AGENTS.md'},
    'development': {'.agents/policies/development.md'},
    'coding': {'.agents/policies/coding.md'},
    'validation': {'.agents/policies/validation.md'},
    'skills': {'.agents/policies/skills.md'},
    'release': {'.agents/policies/release.yaml'},
    'release-runbook': {'.agents/runbooks/release.md'},
}
observed = {}
for row in manifest['files']:
    assert manage.allowed_target(row['target'])
    assert manage.safe_path(root, row['source']).is_file()
    assert row['target'] not in observed.setdefault(row['module'], set())
    observed[row['module']].add(row['target'])
assert observed == expected
# An exact canonical example guards against accidental permission broadening.
release = (root / '.template/modules/release.yaml').read_text()
assert release == '''schema: release-policy/v1
promotion:
  source: develop
  target: main
  pull_request: required
  merge:
    executor: human
    agent_authorization: not-applicable
    auto_merge: forbidden
    method: repository-default
'''
print('Template inventory and release-policy/v1 default: passed')
