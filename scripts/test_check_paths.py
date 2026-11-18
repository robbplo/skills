from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('check-paths.py')


class CheckPathsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pstack-check-paths-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write('docs/harness/claude-code.md', '| The `create-skill` skill | Run `/skill-creator`. |\n')
        self.write('skills/principle-prove-it-works/SKILL.md', '# Prove\n')
        self.write('skills/alpha/SKILL.md', '# Alpha\n')
        self.write('skills/alpha/references/notes.md', 'Notes.\n')

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def run_check(self):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root)], capture_output=True, text=True)
        return result.returncode, result.stdout.splitlines()

    def test_clean_tree_passes(self):
        self.write('skills/alpha/SKILL.md', 'Read `references/notes.md` and the **principle-prove-it-works** skill. Keep `AGENTS.md`.\n')
        self.write('skills/alpha/references/guide.md', 'See `references/notes.md`, `../../docs/harness/claude-code.md`, and the `create-skill` skill.\n')
        self.assertEqual(self.run_check(), (0, []))

    def test_skill_folder_path_that_does_not_exist_fails(self):
        self.write('skills/alpha/SKILL.md', 'Read `playbooks/missing.md`.\n')
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(out, ['skills/alpha/SKILL.md:1: playbooks/missing.md does not resolve from skills/alpha/'])

    def test_paths_relative_to_the_reference_folder_fail(self):
        self.write('skills/alpha/references/guide.md', 'Use `notes.md`.\nSee [notes](./notes.md) and [top](../SKILL.md).\n')
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(out, [
            'skills/alpha/references/guide.md:1: notes.md resolves from references/, not from skills/alpha/',
            'skills/alpha/references/guide.md:2: ./notes.md does not resolve from skills/alpha/',
            'skills/alpha/references/guide.md:2: ../SKILL.md does not resolve from skills/alpha/',
        ])

    def test_every_short_principle_name_fails(self):
        self.write('skills/principle-fix-root-causes/SKILL.md', '# Fix\n')
        self.write('skills/alpha/SKILL.md', 'Per the **fix-root-causes** and **prove-it-works** principle skills.\n')
        _, out = self.run_check()
        self.assertEqual(out, [
            'skills/alpha/SKILL.md:1: **fix-root-causes** names no skill; write **principle-fix-root-causes**',
            'skills/alpha/SKILL.md:1: **prove-it-works** names no skill; write **principle-prove-it-works**',
        ])

    def test_unknown_slash_skill_fails_unless_mapped_or_denied(self):
        self.write('skills/alpha/SKILL.md', 'Chart with `/visualize`. Author with `/skill-creator`. pstack has no `/orchestrate` skill.\n')
        _, out = self.run_check()
        self.assertEqual(out, ['skills/alpha/SKILL.md:1: visualize names no skill in skills/ and has no row in docs/harness/claude-code.md'])

    def test_line_numbers_survive_fenced_blocks(self):
        self.write('skills/alpha/SKILL.md', 'Intro.\n\n```\ncode\n```\nRead `playbooks/missing.md`.\n')
        _, out = self.run_check()
        self.assertEqual(out, ['skills/alpha/SKILL.md:6: playbooks/missing.md does not resolve from skills/alpha/'])


if __name__ == '__main__':
    unittest.main()
