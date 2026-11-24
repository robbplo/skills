#!/usr/bin/env python3
"""PreToolUse guards for pstack. Reads the hook event on stdin and prints a decision, or nothing to allow."""
import json
import re
import shlex
import subprocess
import sys

CROSS_PROJECT = re.compile(r"\.claude/projects/\*")
TRUNKS = {"main", "master", "trunk"}
FORCE = re.compile(r"^(-[a-zA-Z]*f[a-zA-Z]*|--force|--force-with-lease(=.*)?|--force-if-includes)$")


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))


def transcripts(event):
    fields = event.get("tool_input", {})
    if any(CROSS_PROJECT.search(str(fields.get(k, ""))) for k in ("command", "pattern", "path", "glob")):
        decide("deny", "This glob reads every project's transcripts, which holds private chats from unrelated "
                       "projects. Read only this workspace's folder under ~/.claude/projects/. The pstack "
                       "transcript-dir script prints it.")


def current_branch(cwd):
    try:
        return subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd or None,
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def pushes(command):
    for part in re.split(r"&&|\|\||[;|\n]", command):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        if "git" in words and "push" in words[words.index("git"):]:
            yield words[words.index("push", words.index("git")) + 1:]


def force_push(event):
    for args in pushes(event.get("tool_input", {}).get("command", "")):
        refs = [a for a in args if not a.startswith("-")][1:]
        forced = any(FORCE.match(a) for a in args) or any(r.startswith("+") for r in refs)
        targets = {r.lstrip("+").split(":")[-1].removeprefix("refs/heads/") for r in refs} or {current_branch(event.get("cwd"))}
        if forced and targets & TRUNKS:
            decide("ask", "This force-pushes a trunk branch, which rewrites history other people share. "
                          "pstack pauses for the user on irreversible writes.")
            return


if __name__ == "__main__":
    {"transcripts": transcripts, "force-push": force_push}[sys.argv[1]](json.load(sys.stdin))
