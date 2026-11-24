import json
import subprocess
import sys
import unittest
from pathlib import Path

GUARD = Path(__file__).with_name("guard.py")


def run(mode, tool_input, cwd="/"):
    out = subprocess.run([sys.executable, str(GUARD), mode], input=json.dumps({"tool_input": tool_input, "cwd": cwd}),
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None


class Transcripts(unittest.TestCase):
    def test_a_glob_across_projects_is_denied_in_each_tool(self):
        self.assertEqual(run("transcripts", {"command": "rg foo ~/.claude/projects/*/"}), "deny")
        self.assertEqual(run("transcripts", {"pattern": "/Users/a/.claude/projects/*/*.jsonl"}), "deny")
        self.assertEqual(run("transcripts", {"pattern": "foo", "path": "~/.claude/projects/*"}), "deny")

    def test_one_workspace_folder_is_allowed(self):
        self.assertIsNone(run("transcripts", {"command": "rg foo ~/.claude/projects/-Users-a-proj/"}))
        self.assertIsNone(run("transcripts", {"command": "ls ~/.claude/projects"}))


class ForcePush(unittest.TestCase):
    def test_a_forced_push_to_trunk_asks(self):
        for command in ("git push --force origin main", "git push -f origin HEAD:master",
                        "cd x && git push --force-with-lease origin main", "git push origin +main",
                        "git -C repo push -uf origin refs/heads/trunk"):
            self.assertEqual(run("force-push", {"command": command}), "ask", command)

    def test_other_pushes_pass(self):
        for command in ("git push origin main", "git push --force-with-lease origin feature/x",
                        "git push -f origin feature", "git status"):
            self.assertIsNone(run("force-push", {"command": command}), command)


if __name__ == "__main__":
    unittest.main()
