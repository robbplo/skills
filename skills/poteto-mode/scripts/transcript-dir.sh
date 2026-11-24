#!/usr/bin/env bash
# Print the folder that holds Claude Code's transcripts for one workspace.
# Usage: transcript-dir.sh [workspace-path]   (default: the current directory)
set -euo pipefail
workspace=$(cd "${1:-.}" && pwd -P)
printf '%s/projects/%s\n' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "$(printf '%s' "$workspace" | sed 's/[^A-Za-z0-9]/-/g')"
