import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class InstallCodexTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pstack-install-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.home = self.root / 'home'
        self.pack = self.home / '.codex/pstack-local'
        self.catalog = self.home / '.agents/skills'
        for folder in ('scripts', 'skills', 'agents', 'docs/harness', 'assets'):
            (self.source / folder).mkdir(parents=True)
        shutil.copy2(Path(__file__).with_name('install-codex.py'), self.source / 'scripts/install-codex.py')
        (self.source / 'docs/harness/codex.md').write_text('Codex adapter.\n')
        (self.source / 'README.md').write_text('Bundled setup help.\n')
        self.write_skill('alpha')
        self.write_skill('obsolete')

    def write_skill(self, name, text=None):
        path = self.source / 'skills' / name / 'SKILL.md'
        path.parent.mkdir(exist_ok=True)
        path.write_text(text or f'---\nname: {name}\ndescription: "Use {name}."\ndisable-model-invocation: true\n---\n\n# {name}\n')

    def run_install(self, fault=None):
        env = dict(os.environ)
        if fault:
            injection = self.root / 'fault'
            injection.mkdir(exist_ok=True)
            unlink_cleanup = fault in ('cleanup-interrupt', 'rollback-cleanup-interrupt')
            (injection / 'sitecustomize.py').write_text(
                'import os\nimport shutil\nfrom pathlib import Path\n'
                f'fault = {fault!r}\n'
                'failed_publish = False\n'
                'original = os.symlink\n'
                'def symlink(source, target, *args, **kwargs):\n'
                '    global failed_publish\n'
                '    if str(target).endswith("/beta") and fault != "cleanup-interrupt":\n'
                '        failed_publish = True\n'
                + ('        os._exit(91)\n' if fault == 'interrupt' else '        raise OSError("injected catalog failure")\n')
                + '    return original(source, target, *args, **kwargs)\n'
                'os.symlink = symlink\n'
                + (
                    'original_rmtree = shutil.rmtree\n'
                    'def rmtree(path, *args, **kwargs):\n'
                    '    root = Path(path)\n'
                    '    for marker in root.rglob(".pstack-local-install"):\n'
                    '        transaction = (marker.parent / "state.json").is_file()\n'
                    '        discarded_pack = failed_publish and (marker.parent / "skills").is_dir()\n'
                    '        if (fault == "cleanup-interrupt" and transaction) or discarded_pack:\n'
                    '            marker.unlink()\n'
                    '            os._exit(91)\n'
                    '    return original_rmtree(path, *args, **kwargs)\n'
                    'shutil.rmtree = rmtree\n'
                    if unlink_cleanup else ''
                )
            )
            env['PYTHONPATH'] = str(injection)
        return subprocess.run(
            [sys.executable, str(self.source / 'scripts/install-codex.py'), '--home', str(self.home)],
            capture_output=True, text=True, env=env,
        )

    def assert_installs(self):
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)

    def snapshot(self):
        entries = {}
        for root in (self.pack, self.catalog):
            for path in root.rglob('*'):
                if path.is_symlink():
                    entries[str(path.relative_to(self.home))] = ('link', os.readlink(path))
                elif path.is_file():
                    entries[str(path.relative_to(self.home))] = ('file', path.read_bytes())
        return entries

    def test_installs_readme_and_final_adapter_paths(self):
        self.assert_installs()
        self.assertEqual((self.pack / 'README.md').read_text(), 'Bundled setup help.\n')
        skill = (self.pack / 'skills/alpha/SKILL.md').read_text()
        self.assertIn(str(self.pack / 'docs/harness/codex.md'), skill)
        self.assertTrue((self.catalog / 'alpha').samefile(self.pack / 'skills/alpha'))
        self.assertEqual((self.pack / 'skills/alpha/agents/openai.yaml').read_text(), 'policy:\n  allow_implicit_invocation: false\n')

    def test_malformed_update_preserves_pack_and_catalog(self):
        self.assert_installs()
        before = self.snapshot()
        self.write_skill('aaa-malformed', '---\nname: aaa-malformed\n')
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_missing_required_metadata_preserves_pack(self):
        self.assert_installs()
        before = self.snapshot()
        self.write_skill('alpha', '---\nname: alpha\n---\n# Missing description\n')
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_copy_failure_preserves_pack_and_catalog(self):
        self.assert_installs()
        before = self.snapshot()
        shutil.rmtree(self.source / 'assets')
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_removed_skills_prune_only_owned_links(self):
        self.assert_installs()
        unrelated = self.catalog / 'unrelated'
        unrelated.symlink_to(self.root / 'other-skill')
        shutil.rmtree(self.source / 'skills/obsolete')
        self.assert_installs()
        self.assertFalse(os.path.lexists(self.catalog / 'obsolete'))
        self.assertEqual(os.readlink(unrelated), str(self.root / 'other-skill'))
        self.assertTrue((self.catalog / 'alpha').exists())

    def test_reinstall_preserves_models_and_is_idempotent(self):
        self.assert_installs()
        (self.pack / 'models.md').write_text('how explorer: inherit-parent\n')
        before = self.snapshot()
        self.assert_installs()
        self.assertEqual(self.snapshot(), before)

    def test_collision_preserves_unrelated_installation(self):
        collision = self.catalog / 'alpha'
        collision.mkdir(parents=True)
        (collision / 'keep').write_text('Unrelated.\n')
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertFalse(self.pack.exists())
        self.assertEqual((collision / 'keep').read_text(), 'Unrelated.\n')

    def test_refuses_unrelated_pack(self):
        self.pack.mkdir(parents=True)
        (self.pack / 'keep').write_text('Unrelated pack.\n')
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual((self.pack / 'keep').read_text(), 'Unrelated pack.\n')

    def test_fresh_link_failure_removes_partial_pack_and_owned_links(self):
        self.write_skill('beta')
        self.assertNotEqual(self.run_install('failure').returncode, 0)
        self.assertFalse(self.pack.exists())
        self.assertEqual(list(self.catalog.iterdir()), [])
        self.assert_installs()

    def test_link_failure_restores_previous_pack_and_catalog(self):
        self.assert_installs()
        before = self.snapshot()
        self.write_skill('beta')
        shutil.rmtree(self.source / 'skills/obsolete')
        self.assertNotEqual(self.run_install('failure').returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_interrupted_publish_recovers_before_validating_next_update(self):
        self.assert_installs()
        before = self.snapshot()
        self.write_skill('beta')
        shutil.rmtree(self.source / 'skills/obsolete')
        self.assertEqual(self.run_install('interrupt').returncode, 91)
        self.write_skill('aaa-malformed', '---\nname: aaa-malformed\n')
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_interrupted_success_cleanup_does_not_block_reinstall(self):
        self.assert_installs()
        before = self.snapshot()
        self.assertEqual(self.run_install('cleanup-interrupt').returncode, 91)
        self.assert_installs()
        self.assertEqual(self.snapshot(), before)

    def test_interrupted_rollback_cleanup_preserves_previous_install(self):
        self.assert_installs()
        before = self.snapshot()
        self.write_skill('beta')
        shutil.rmtree(self.source / 'skills/obsolete')
        self.assertEqual(self.run_install('rollback-cleanup-interrupt').returncode, 91)
        self.write_skill('aaa-malformed', '---\nname: aaa-malformed\n')
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
