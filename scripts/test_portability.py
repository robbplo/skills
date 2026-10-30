"""Portability and global-instruction installation checks (temporary homes only)."""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HOST_LABELS = {'codex': 'Codex', 'claude-code': 'Claude Code'}
sys.dont_write_bytecode = True


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load('installer', 'install-codex.py')
instructions = load('instructions', 'install-instructions.py')


class PortabilityTest(unittest.TestCase):
    def test_skills_and_agents_have_no_adapter_preludes(self):
        paths = list((ROOT / 'skills').glob('*/SKILL.md')) + list((ROOT / 'agents').glob('*.md'))
        for path in paths:
            with self.subTest(path=path):
                if path.name == 'SKILL.md':
                    installer.skill_frontmatter(path)
                text = path.read_text()
                self.assertNotIn('Before executing, read the [host contract]', text)
                self.assertNotIn('active host adapter before working', text)
                self.assertNotIn('## Host instructions', text)

    def test_contract_links_resolve(self):
        for path in (ROOT / 'docs/harness').glob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' not in target:
                    self.assertTrue((path.parent / target.split('#')[0]).exists(), (path, target))

    def test_codex_install_has_clean_skills_and_global_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            installer.install(home)
            pack = home / '.codex/pstack-local'
            for source in (ROOT / 'skills').glob('*/SKILL.md'):
                installed = pack / 'skills' / source.parent.name / 'SKILL.md'
                text = installed.read_text()
                self.assertNotIn('## Host instructions', text)
                self.assertNotIn('select the active host adapter', text)
                self.assertEqual(installer.skill_frontmatter(source)[1].strip(),
                                 installer.skill_frontmatter(installed)[1].strip())
                if 'disable-model-invocation: true' in source.read_text():
                    self.assertIn('disable-model-invocation: true', text)
            self.assertIn('## Codex runtime rules', (home / '.codex/AGENTS.md').read_text())

    def test_versions_match(self):
        versions = [json.loads((ROOT / path).read_text())['version'] for path in
                    ('plugin.json', '.cursor-plugin/plugin.json', '.claude-plugin/plugin.json')]
        self.assertEqual(len(set(versions)), 1)

    def test_plan_host_aliases_use_portable_requirements(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / 'plan.md'
            plan.write_text('# Incomplete plan\n')
            outputs = []
            for host in ('codex', 'portable', 'claude-code'):
                result = subprocess.run(['node', str(ROOT / 'skills/poteto-mode/scripts/check-plan.mjs'),
                                         '--host', host, str(plan)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                outputs.append((result.stdout, result.stderr))
            self.assertTrue(all(output == outputs[0] for output in outputs))


class InstructionsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='pstack-instructions-test-')
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name) / 'home'

    def target(self, host='codex'):
        return self.home / instructions.HOSTS[host]['global']

    def put(self, text, host='codex'):
        target = self.target(host)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode())
        return target

    def snapshot(self):
        if not self.home.exists():
            return {}
        return {str(path.relative_to(self.home)): ('link', os.readlink(path)) if path.is_symlink()
                else ('file', path.read_bytes()) if path.is_file() else ('dir',)
                for path in self.home.rglob('*')}

    def test_full_selected_rules_absolute_paths_and_idempotence(self):
        for host, config in instructions.HOSTS.items():
            with self.subTest(host=host), patch.dict(os.environ, {'CLAUDE_PLUGIN_ROOT': ''}):
                instructions.install(self.home, [host])
                target = self.target(host)
                first = target.read_text()
                self.assertIn('## Shared compatibility rules', first)
                self.assertIn(f'## {HOST_LABELS[host]} runtime rules', first)
                self.assertIn(str(self.home / config['pack']), first)
                self.assertNotIn('<pstack>', first)
                self.assertNotIn('<project-skills>', first)
                self.assertNotIn('~/', first)
                self.assertNotIn('$HOME/', first)
                self.assertNotIn('Setup prerequisite:', first)
                self.assertNotIn('Read the [host contract]', first)
                self.assertIn('Do not assume delegates inherit these rules.', first)
                for other in instructions.HOSTS.keys() - {host}:
                    self.assertNotIn(f'## {HOST_LABELS[other]} runtime rules', first)
                before = target.stat().st_mtime_ns
                instructions.install(self.home, [host])
                self.assertEqual(target.read_text(), first)
                self.assertEqual(target.stat().st_mtime_ns, before)
                if host == 'codex':
                    self.assertLess(len(first.encode()), 24 * 1024)  # leave room in Codex's 32KiB context budget

    def test_preserves_outside_prose_and_file_mode(self):
        begin, end = instructions.BEGIN, instructions.END
        prefix, suffix = '# Personal\r\nKeep exactly.\r\n\n', '\n\nTrailing prose without newline'
        target = self.put(prefix + begin + '\nold rules\n' + end + suffix)
        target.chmod(0o640)
        instructions.install(self.home, ['codex'])
        content = target.read_bytes().decode()
        self.assertTrue(content.startswith(prefix + begin))
        self.assertTrue(content.endswith(end + suffix))
        self.assertNotIn('old rules', content)
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)

    def test_appends_without_damaging_unrelated_content(self):
        for existing in ('', 'Personal without newline', 'Personal\n', 'Personal\n\n'):
            with self.subTest(existing=existing):
                result = instructions.render_section(existing, 'Rules')
                self.assertTrue(result.startswith(existing))
                self.assertEqual(result.count(instructions.BEGIN), 1)
                self.assertEqual(instructions.render_section(result, 'Rules'), result)

    def test_malformed_boundaries_refused_without_mutation(self):
        begin, end = instructions.BEGIN, instructions.END
        for malformed in (begin, end, end + '\n' + begin,
                          begin + '\n' + begin + '\n' + end + '\n' + end,
                          begin + '\n' + end + '\n' + begin + '\n' + end,
                          ' ' + begin + '\n' + end,
                          begin.replace(' -->', '-->') + '\n' + end):
            with self.subTest(malformed=malformed):
                self.put(malformed, 'claude-code')
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    instructions.install(self.home, ['codex', 'claude-code'])
                self.assertEqual(self.snapshot(), before)

    def test_symlink_file_and_parent_refused_without_mutation(self):
        outside = self.home.parent / 'nix-managed'
        outside.write_text('Keep outside')
        target = self.target()
        target.parent.mkdir(parents=True)
        target.symlink_to(outside)
        before = self.snapshot()
        with self.assertRaises(ValueError):
            instructions.install(self.home, ['codex'])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(outside.read_text(), 'Keep outside')
        target.unlink()
        target.parent.rmdir()
        target.parent.symlink_to(self.home.parent / 'missing-directory', target_is_directory=True)
        before = self.snapshot()
        with self.assertRaises(ValueError):
            instructions.install(self.home, ['codex'])
        self.assertEqual(self.snapshot(), before)

    def test_directory_and_invalid_utf8_refused(self):
        target = self.target()
        target.mkdir(parents=True)
        before = self.snapshot()
        with self.assertRaises(ValueError):
            instructions.install(self.home, ['codex'])
        self.assertEqual(self.snapshot(), before)
        target.rmdir()
        target.write_bytes(b'\xff')
        with self.assertRaises(ValueError):
            instructions.install(self.home, ['codex'])
        self.assertEqual(target.read_bytes(), b'\xff')

    def test_missing_runtime_rules_does_not_create_home(self):
        with self.assertRaises(FileNotFoundError):
            instructions.prepare(self.home, 'codex', source=self.home.parent / 'missing-source')
        self.assertFalse(self.home.exists())

    def test_failed_atomic_write_preserves_original(self):
        target = self.put('Personal\n')
        before = self.snapshot()
        with patch.object(instructions.os, 'replace', side_effect=OSError('injected write failure')):
            with self.assertRaises(OSError):
                instructions.install(self.home, ['codex'])
        self.assertEqual(target.read_text(), 'Personal\n')
        self.assertEqual(self.snapshot(), before)

    def test_detects_changed_file_before_publication(self):
        target = self.put('Personal\n')
        prepared = instructions.prepare(self.home, 'codex')
        target.write_text('Concurrent edit\n')
        with self.assertRaises(ValueError):
            instructions.publish(prepared, self.home)
        self.assertEqual(target.read_text(), 'Concurrent edit\n')

    def test_claude_pack_override_and_environment(self):
        plugin = self.home.parent / 'actual-plugin'
        with patch.dict(os.environ, {'CLAUDE_PLUGIN_ROOT': str(plugin)}):
            instructions.install(self.home, ['claude-code'])
            self.assertIn(f'The installed pack is `{plugin}`.', self.target('claude-code').read_text())
            override = self.home.parent / 'explicit-pack'
            instructions.install(self.home, ['claude-code'], override)
            self.assertIn(f'The installed pack is `{override}`.', self.target('claude-code').read_text())
            self.assertNotIn(f'The installed pack is `{plugin}`.', self.target('claude-code').read_text())

    def test_cli_host_selection_and_pack_override(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/install-instructions.py'),
                                 '--home', str(self.home), '--host', 'claude-code', '--pack', str(ROOT)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'The installed pack is `{ROOT}`.', self.target('claude-code').read_text())
        self.assertFalse(self.target('codex').exists())

    def test_codex_instruction_write_failure_rolls_back_pack(self):
        installer.install(self.home)
        self.put('Personal rules\n')
        before = self.snapshot()
        with patch.object(installer.instructions, 'publish', side_effect=OSError('injected instruction failure')):
            with self.assertRaises(OSError):
                installer.install(self.home)
        # The managed lock file may be opened, but its content and all installation state stay unchanged.
        self.assertEqual(self.snapshot(), before)

    def test_codex_rejects_unsafe_instructions_before_installing_pack(self):
        self.put(instructions.BEGIN)
        before = self.snapshot()
        with self.assertRaises(ValueError):
            installer.install(self.home)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
