#!/usr/bin/env python3
"""Hooks for work on this repo. Exit 2 sends stderr back to the agent."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = ("plugin.json", ".claude-plugin/plugin.json")


def paths(event):
    edited = Path(event.get("tool_input", {}).get("file_path", "")).resolve()
    if not edited.is_relative_to(ROOT / "skills"):
        return
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check-paths.py")], capture_output=True, text=True)
    if result.returncode:
        sys.exit(fail("check-paths.py reports:\n" + result.stdout))


def version(_event):
    versions = {m: json.loads((ROOT / m).read_text())["version"] for m in MANIFESTS}
    if len(set(versions.values())) > 1:
        sys.exit(fail(f"The manifests disagree on version: {versions}. AGENTS.md needs them identical."))
    trunk = subprocess.run(["git", "show", "origin/main:plugin.json"], cwd=ROOT, capture_output=True, text=True)
    if trunk.returncode == 0 and json.loads(trunk.stdout)["version"] == versions["plugin.json"]:
        sys.exit(fail(f"The plugin version is still {versions['plugin.json']}, the same as origin/main. "
                      "AGENTS.md needs every PR to bump it in both manifests."))


def fail(message):
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    {"paths": paths, "version": version}[sys.argv[1]](json.load(sys.stdin))
