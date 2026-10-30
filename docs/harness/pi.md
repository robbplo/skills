# pstack in Pi

Install this checkout with `pi install /absolute/path/to/skills`, or install the repository with `pi install git:github.com/robbplo/skills`. Restart Pi or run `/reload`, then use `/skill:poteto-mode <task>`, `/skill:poteto-help`, or `/skill:setup-pstack`. The package exposes only `skills/`, not the dormant automation pack.

Setup prerequisite: run `python3 scripts/install-instructions.py --host pi --pack /absolute/installed/pack` from the checkout to install the full shared and Pi rules in `~/.pi/agent/AGENTS.md`. For `pi install /absolute/path/to/skills`, use that same checkout path as `--pack`, since Pi loads local packages in place. For a Git package, use the installed pack directory shown by `pi list`. Omit `--pack` only for a full copied pack already installed at `~/.pi/agent/skills/pstack`. Refresh any manually copied pack from this checkout to remove stale generated host preludes. Reload Pi after setup. No per-skill adapter reads are needed.

If Pi already discovers the Codex install through `~/.agents/skills`, do not install a duplicate copy. Install Pi global instructions with `--pack /absolute/path/to/the/shared/pack`; the Pi rules apply regardless of the pack's installation path.

<!-- pstack:runtime -->

## Pi runtime rules

Use Pi's available `read`, `bash`, `edit`, and `write` tools for file work. Resolve all relative skill paths against the loaded skill's directory. Read sibling skills directly rather than sending slash commands to a shell.

Pi does not require a delegation extension. Inspect the current tools before using workers; do not assume `Task`, `spawn_agent`, background agents, or a particular extension exists. When no delegation tool exists, work sequentially and report independent-review gates as unmet. If an extension provides workers, follow its schema and pass the applicable loaded rules and absolute skill and agent-brief paths to each worker. Do not start nested Pi processes to bypass missing capabilities.

Models inherit the session by default. Read `~/.config/pstack/models.md` when present. Setup uses the role labels from `setup-pstack`, with `inherit-parent` for scalar roles and two `inherit-parent` entries for panel roles. Confirm choices and write plain Markdown without frontmatter. Only offer model or effort overrides verified against the installed delegation tool; Pi's session model availability alone does not prove workers accept overrides. Report unsupported budget controls rather than changing Pi settings. Keep configuration outside the package so updates preserve it.

Use a checklist for plans and plain text for questions unless a tool provides those operations. Use a verified event watcher or bounded polling only while the session is active; checkpoint before stopping. No persistent wakes or cloud machines are implied.

Use `.pi/skills/` for generated project skills and `AGENTS.md` for project instructions. For history-based work use the current session context or an explicit workspace-matched session path from the host/user. Session directories are configurable; do not guess or scan all of `~/.pi`.

Run helper scripts with `--host portable` per the shared rules. Forge operations use available repository tooling such as `gh`. Cursor automation provisioning remains unavailable unless the user explicitly supplies that integration. Never represent a sequential check as independent review.
