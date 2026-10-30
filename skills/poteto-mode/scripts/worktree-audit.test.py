import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('worktree-audit.sh')


class WorktreeAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='worktree-audit-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.home = self.root / 'home'
        self.repo = self.root / 'repo'
        self.worktree = self.root / 'active'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.home.mkdir()
        self.repo.mkdir()
        self.env = dict(os.environ, HOME=str(self.home),
                        CODEX_HOME=str(self.home / '.codex'),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                        PATH=str(self.bin) + os.pathsep + os.environ['PATH'])
        for name in ('gh', 'origin'):
            stub = self.bin / name
            stub.write_text('#!/bin/sh\nexit 1\n')
            stub.chmod(0o755)
        self.rg_log = self.root / 'history-reads'
        self.env['AUDIT_RG_LOG'] = str(self.rg_log)
        self.env['AUDIT_REAL_RG'] = shutil.which('rg')
        rg = self.bin / 'rg'
        rg.write_text('#!/bin/sh\nprintf "read\\n" >> "$AUDIT_RG_LOG"\nexec "$AUDIT_REAL_RG" "$@"\n')
        rg.chmod(0o755)
        for args in (['init', '-b', 'main'], ['config', 'user.email', 'fixture@example.invalid'],
                     ['config', 'user.name', 'Fixture']):
            self.git(*args)
        (self.repo / 'tracked.txt').write_text('committed\n')
        self.git('add', 'tracked.txt')
        self.git('commit', '-m', 'Fixture')
        self.git('worktree', 'add', '-b', 'active', str(self.worktree))
        slug = str(self.repo).lstrip('/').replace('/', '-')
        cursor = self.home / '.cursor/projects' / slug / 'agent-transcripts/chat record.jsonl'
        cursor.parent.mkdir(parents=True)
        cursor.write_text(json.dumps({'cwd': str(self.worktree)}) + '\n')
        codex = self.home / '.codex/sessions/2026/10/27/session.jsonl'
        codex.parent.mkdir(parents=True)
        codex.write_text(json.dumps({'type': 'session_meta', 'payload': {'cwd': str(self.worktree)}}) + '\n')

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.repo), *args], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def audit(self, *args):
        return subprocess.run(['bash', str(SCRIPT), *args, '-b', 'main', str(self.repo)],
                              env=self.env, capture_output=True, text=True)

    def row(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [line.split('\t') for line in result.stdout.splitlines()
                if not line.startswith('#')]
        self.assertEqual(len(rows), 2, result.stdout)
        row = dict(zip(rows[0], rows[1]))
        self.assertEqual(row['WORKTREE'], str(self.worktree))
        return row

    def test_codex_activity_stays_unknown_without_reading_cursor_history(self):
        row = self.row(self.audit('--host', 'codex'))
        self.assertEqual(row['MERGED'], 'YES')
        self.assertEqual(row['LAST_CHAT'], 'unknown')
        self.assertEqual(row['BUCKET'], 'verify-activity')
        self.assertFalse(self.rg_log.exists())

    def test_claude_activity_stays_unknown_without_reading_cursor_history(self):
        row = self.row(self.audit('--host', 'claude'))
        self.assertEqual(row['LAST_CHAT'], 'unknown')
        self.assertEqual(row['BUCKET'], 'verify-activity')
        self.assertFalse(self.rg_log.exists())

    def test_unspecified_host_stays_unknown_without_reading_cursor_history(self):
        row = self.row(self.audit())
        self.assertEqual(row['LAST_CHAT'], 'unknown')
        self.assertEqual(row['BUCKET'], 'verify-activity')
        self.assertFalse(self.rg_log.exists())

    def test_explicit_cursor_recognizes_recent_chat(self):
        row = self.row(self.audit('--host', 'cursor'))
        self.assertNotEqual(row['LAST_CHAT'], '-')
        self.assertNotEqual(row['LAST_CHAT'], 'unknown')
        self.assertEqual(row['BUCKET'], 'verify-recent-chat')
        self.assertTrue(self.rg_log.exists())

    def test_codex_keeps_tracked_work_on_hold(self):
        (self.worktree / 'tracked.txt').write_text('work in progress\n')
        row = self.row(self.audit('--host', 'codex'))
        self.assertEqual(row['BUCKET'], 'hold-wip')
        self.assertEqual(row['LAST_CHAT'], 'unknown')

    def test_worktree_paths_keep_spaces(self):
        spaced = self.root / 'active worktree'
        self.git('worktree', 'move', str(self.worktree), str(spaced))
        self.worktree = spaced
        row = self.row(self.audit('--host', 'codex'))
        self.assertEqual(row['BUCKET'], 'verify-activity')

    def test_codex_keeps_open_pr_on_hold(self):
        origin = self.bin / 'origin'
        origin.write_text('#!/bin/sh\nprintf \'%s\\n\' \'[{"number":1,"status":"open","headRef":"active"}]\'\n')
        row = self.row(self.audit('--host', 'codex'))
        self.assertEqual(row['BUCKET'], 'hold-open-pr')
        self.assertEqual(row['LAST_CHAT'], 'unknown')

    def test_invalid_or_missing_host_is_a_usage_error(self):
        for args in (('--host', 'other'), ('--host',)):
            result = self.audit(*args)
            self.assertEqual(result.returncode, 2)
            self.assertIn('host', result.stderr)
        self.assertFalse(self.rg_log.exists())


if __name__ == '__main__':
    unittest.main()
