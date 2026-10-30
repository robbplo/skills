"""Static portability and shared-install regression checks (no live host required)."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install-codex.py')
installer = importlib.util.module_from_spec(spec)
sys.dont_write_bytecode = True
spec.loader.exec_module(installer)


class PortabilityTest(unittest.TestCase):
    def test_host_sensitive_entry_points_load_contract(self):
        for path in (ROOT / 'skills').glob('*/SKILL.md'):
            installer.skill_frontmatter(path)
            text = path.read_text()
            if re.search(r'Task|Cursor|\.cursor|subagent|AskQuestion|TodoWrite', text):
                with self.subTest(skill=path.parent.name):
                    self.assertIn('[host contract](../../docs/harness/README.md)', text)
        for path in (ROOT / 'agents').glob('*.md'):
            self.assertIn('[host contract](../docs/harness/README.md)', path.read_text())

    def test_contract_links_resolve(self):
        for path in (ROOT / 'docs/harness').glob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' not in target:
                    self.assertTrue((path.parent / target.split('#')[0]).exists(), (path, target))

    def test_shared_install_selects_runtime_host_and_preserves_pi_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            installer.install(home)
            pack = home / '.codex/pstack-local'
            for source in (ROOT / 'skills').glob('*/SKILL.md'):
                installed = pack / 'skills' / source.parent.name / 'SKILL.md'
                text = installed.read_text()
                self.assertIn(str(pack / 'docs/harness/README.md'), text)
                self.assertIn('select the active host adapter', text)
                if 'disable-model-invocation: true' in source.read_text():
                    self.assertIn('disable-model-invocation: true', text)
            self.assertTrue((pack / 'docs/harness/pi.md').is_file())

    def test_pi_manifest_limits_discovery(self):
        manifest = json.loads((ROOT / 'package.json').read_text())
        self.assertEqual(manifest['pi'], {
            'skills': ['./skills'], 'extensions': [], 'prompts': [], 'themes': []})

    def test_versions_match(self):
        versions = [json.loads((ROOT / path).read_text())['version'] for path in
                    ('plugin.json', '.cursor-plugin/plugin.json', '.claude-plugin/plugin.json')]
        self.assertEqual(len(set(versions)), 1)

    def test_plan_host_aliases_use_portable_requirements(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / 'plan.md'
            plan.write_text('# Incomplete plan\n')
            outputs = []
            for host in ('codex', 'portable', 'pi', 'claude-code'):
                result = subprocess.run(['node', str(ROOT / 'skills/poteto-mode/scripts/check-plan.mjs'),
                                         '--host', host, str(plan)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                outputs.append((result.stdout, result.stderr))
            self.assertTrue(all(output == outputs[0] for output in outputs))


if __name__ == '__main__':
    unittest.main()
