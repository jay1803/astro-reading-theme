import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('manage', ROOT / '.template/manage.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.source = self.base / 'source'
        self.target = self.base / 'target'
        self.target.mkdir()
        shutil.copytree(ROOT, self.source, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        self.git('init', '-q')
        self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args], stderr=subprocess.PIPE)

    def commit(self):
        self.git('add', '--', 'AGENTS.md', '.template', 'README.md', '.gitignore')
        self.git('-c', 'user.name=Template Test', '-c', 'user.email=test@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')

    def run_plan(self, modules=(), apply=False):
        receipt, writes, before = m.plan(self.source, self.target, modules)
        if apply:
            m.apply(self.target, writes, before)
        return {x['path']: x['status'] for x in receipt['actions']}, writes

    def write(self, path, data):
        p = self.target / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data)
        return p

    def test_preview_is_read_only_and_modules_optional(self):
        statuses, writes = self.run_plan()
        self.assertEqual(list(self.target.iterdir()), [])
        self.assertEqual(set(writes), {'AGENTS.md', m.STATE})
        self.assertEqual(statuses['AGENTS.md'], 'create')

    def test_init_and_repeat_are_idempotent(self):
        self.run_plan(['coding'], True)
        self.assertTrue((self.target / '.agents/policies/coding.md').is_file())
        self.assertFalse((self.target / '.agents/policies/release.yaml').exists())
        _, writes = self.run_plan()
        self.assertEqual(writes, {})

    def test_existing_agents_content_and_unrelated_files_survive(self):
        custom = '# Project\nUse pnpm.\n'
        p = self.write('AGENTS.md', custom)
        unrelated = self.write('.agents/skills/my-skill/SKILL.md', 'user owned')
        self.run_plan(apply=True)
        self.assertTrue(p.read_text().startswith(custom))
        self.assertEqual(unrelated.read_text(), 'user owned')
        self.assertEqual(p.read_text().count(m.BEGIN), 1)

    def test_existing_policy_is_not_adopted_or_replaced(self):
        p = self.write('.agents/policies/release.yaml', 'local policy')
        statuses, _ = self.run_plan(['release'], True)
        self.assertEqual(statuses[str(p.relative_to(self.target))], 'preserve-existing')
        self.assertEqual(p.read_text(), 'local policy')
        self.assertNotIn(str(p.relative_to(self.target)), json.loads((self.target/m.STATE).read_text())['files'])

    def test_local_edits_and_deletions_survive(self):
        self.run_plan(['coding', 'validation'], True)
        self.write('.agents/policies/coding.md', 'custom coding rules')
        (self.target / '.agents/policies/validation.md').unlink()
        statuses, _ = self.run_plan(apply=True)
        self.assertEqual(statuses['.agents/policies/coding.md'], 'preserve-local')
        self.assertEqual(statuses['.agents/policies/validation.md'], 'preserve-deleted')
        self.assertFalse((self.target / '.agents/policies/validation.md').exists())

    def test_deleted_agents_block_is_not_resurrected(self):
        self.run_plan(apply=True)
        self.write('AGENTS.md', 'replacement instructions')
        statuses, _ = self.run_plan(apply=True)
        self.assertEqual(statuses['AGENTS.md'], 'preserve-deleted')
        self.assertEqual((self.target/'AGENTS.md').read_text(), 'replacement instructions')

    def test_upstream_core_update_preserves_agents_surroundings(self):
        self.run_plan(apply=True)
        p = self.target/'AGENTS.md'
        p.write_text('before\n' + p.read_text() + 'after\n')
        src = self.source/'AGENTS.md'
        src.write_text(src.read_text().replace('## Repository guidance', '## Updated repository guidance'))
        self.commit()
        statuses, _ = self.run_plan(apply=True)
        self.assertEqual(statuses['AGENTS.md'], 'update')
        self.assertTrue(p.read_text().startswith('before\n'))
        self.assertTrue(p.read_text().endswith('after\n'))
        self.assertIn('## Updated repository guidance', p.read_text())

    def test_upstream_policy_update_requires_review(self):
        self.run_plan(['release'], True)
        target = self.target/'.agents/policies/release.yaml'
        before = target.read_bytes()
        source = self.source/'.template/modules/release.yaml'
        source.write_text(source.read_text() + '# upstream update\n')
        self.commit()
        statuses, _ = self.run_plan(apply=True)
        self.assertEqual(statuses['.agents/policies/release.yaml'], 'policy-review-required')
        self.assertEqual(target.read_bytes(), before)

    def test_retired_module_stays_on_disk(self):
        self.run_plan(['coding'], True)
        p = self.source/'.template/manifest.json'
        manifest = json.loads(p.read_text())
        manifest['files'] = [x for x in manifest['files'] if x['module'] != 'coding']
        p.write_text(json.dumps(manifest))
        self.commit()
        statuses, _ = self.run_plan(apply=True)
        self.assertEqual(statuses['.agents/policies/coding.md'], 'preserve-retired')
        self.assertTrue((self.target/'.agents/policies/coding.md').is_file())

    def test_symlink_parent_rejected_without_external_writes(self):
        outside = self.base/'outside'
        outside.mkdir()
        (self.target/'.agents').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_plan(apply=True)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.target/'AGENTS.md').exists())

    def test_malformed_state_rejected_before_any_writes(self):
        p = self.write(m.STATE, '{"schema":"bad"}')
        with self.assertRaises(ValueError):
            self.run_plan(apply=True)
        self.assertFalse((self.target/'AGENTS.md').exists())
        self.assertEqual(p.read_text(), '{"schema":"bad"}')

    def test_invalid_markers_are_not_silently_appended(self):
        self.write('AGENTS.md', m.BEGIN + '\nmissing end')
        with self.assertRaises(ValueError):
            self.run_plan(apply=True)
        self.assertFalse((self.target/m.STATE).exists())

    def test_duplicate_json_keys_rejected(self):
        self.write(m.STATE, '{"schema":"one","schema":"two"}')
        with self.assertRaises(ValueError):
            self.run_plan(apply=True)

    def test_unsafe_manifest_target_rejected(self):
        p = self.source/'.template/manifest.json'
        manifest = json.loads(p.read_text())
        manifest['files'][0]['target'] = '../outside'
        p.write_text(json.dumps(manifest))
        self.commit()
        with self.assertRaises(ValueError):
            self.run_plan(apply=True)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_dirty_source_rejected(self):
        (self.source/'AGENTS.md').write_text('uncommitted')
        with self.assertRaises(ValueError):
            self.run_plan(apply=True)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_target_changed_since_plan_rejected(self):
        _, writes, before = m.plan(self.source, self.target, [])
        self.write('AGENTS.md', 'concurrent work')
        with self.assertRaises(ValueError):
            m.apply(self.target, writes, before)
        self.assertEqual((self.target/'AGENTS.md').read_text(), 'concurrent work')
        self.assertFalse((self.target/m.STATE).exists())

    def test_replacement_does_not_mutate_a_hardlink(self):
        self.run_plan(apply=True)
        linked = self.base/'external-linked-file'
        os.link(self.target/'AGENTS.md', linked)
        before = linked.read_bytes()
        source = self.source/'AGENTS.md'
        source.write_text(source.read_text().replace('## Repository guidance', '## Upstream clarification'))
        self.commit()
        self.run_plan(apply=True)
        self.assertEqual(linked.read_bytes(), before)
        self.assertNotEqual((self.target/'AGENTS.md').read_bytes(), before)

    def legacy_index(self, content='Unique rule: manual deployment only.\n'):
        self.run_plan(apply=True)
        self.write(m.LEGACY_INDEX, content)
        state_path = self.target / m.STATE
        state = json.loads(state_path.read_text())
        state['files'][m.LEGACY_INDEX] = {
            'module': 'core', 'revision': 'a' * 40, 'sha256': m.digest(content.encode())}
        state_path.write_text(json.dumps(state))

    def test_new_adoption_has_one_index(self):
        self.run_plan(apply=True)
        self.assertFalse((self.target/m.LEGACY_INDEX).exists())
        self.assertNotIn(m.LEGACY_INDEX, json.loads((self.target/m.STATE).read_text())['files'])

    def test_legacy_index_content_is_never_deleted(self):
        self.legacy_index()
        statuses, _ = self.run_plan(apply=True)
        self.assertEqual(statuses[m.LEGACY_INDEX], 'preserve-retired')
        self.assertEqual((self.target/m.LEGACY_INDEX).read_text(), 'Unique rule: manual deployment only.\n')

    def test_legacy_root_keeps_reaching_custom_index_until_migrated(self):
        self.legacy_index()
        old_root = (m.BEGIN + '\nRead [rules](.agents/README.md).\n' + m.END + '\n').encode()
        (self.target/'AGENTS.md').write_bytes(old_root)
        state_path = self.target/m.STATE
        state = json.loads(state_path.read_text())
        state['files']['AGENTS.md']['sha256'] = m.digest(m.block(old_root))
        state_path.write_text(json.dumps(state))
        statuses, _ = self.run_plan(apply=True)
        self.assertEqual(statuses['AGENTS.md'], 'index-migration-required')
        self.assertEqual((self.target/'AGENTS.md').read_bytes(), old_root)
        self.assertIn('manual deployment only', (self.target/m.LEGACY_INDEX).read_text())

    def test_migrated_legacy_index_record_is_retired_and_not_resurrected(self):
        self.legacy_index()
        root = self.target/'AGENTS.md'
        # Deliberate semantic migration removes the old path mention and moves content.
        root.write_text(root.read_text().replace(m.LEGACY_INDEX, 'a secondary index') + '\nUnique rule: manual deployment only.\n')
        (self.target/m.LEGACY_INDEX).unlink()
        statuses, _ = self.run_plan(apply=True)
        self.assertEqual(statuses[m.LEGACY_INDEX], 'retired-removed')
        self.assertNotIn(m.LEGACY_INDEX, json.loads((self.target/m.STATE).read_text())['files'])
        _, writes = self.run_plan()
        self.assertEqual(writes, {})
        self.assertFalse((self.target/m.LEGACY_INDEX).exists())
        self.assertIn('manual deployment only', root.read_text())

    def test_old_index_reference_keeps_retirement_pending(self):
        self.legacy_index()
        (self.target/m.LEGACY_INDEX).unlink()
        root = self.target/'AGENTS.md'
        root.write_text(root.read_text() + '\nRead [rules](.agents/README.md).\n')
        statuses, _ = self.run_plan(apply=True)
        self.assertEqual(statuses[m.LEGACY_INDEX], 'preserve-retired')
        self.assertIn(m.LEGACY_INDEX, json.loads((self.target/m.STATE).read_text())['files'])

    def test_legacy_index_symlink_is_rejected(self):
        self.legacy_index()
        path = self.target/m.LEGACY_INDEX
        path.unlink()
        external = self.base/'external'
        external.write_text('keep this')
        path.symlink_to(external)
        with self.assertRaises(ValueError):
            self.run_plan(apply=True)
        self.assertEqual(external.read_text(), 'keep this')

    def test_unknown_module_rejected(self):
        with self.assertRaises(ValueError):
            self.run_plan(['not-a-module'], True)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_cli_preview_apply_and_attention_exit_codes(self):
        cmd = ['python3', str(self.source/'.template/manage.py'), '--target', str(self.target)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.target.iterdir()), [])
        result = subprocess.run(cmd + ['--apply'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write('AGENTS.md', 'custom root rules')
        result = subprocess.run(cmd + ['--apply'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual((self.target/'AGENTS.md').read_text(), 'custom root rules')


if __name__ == '__main__':
    unittest.main()
