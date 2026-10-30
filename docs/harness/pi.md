# pstack in Pi

Install this checkout with `pi install /absolute/path/to/skills`, or install the repository with `pi install git:github.com/robbplo/skills`. Restart Pi or run `/reload`, then use `/skill:poteto-mode <task>`, `/skill:poteto-help`, or `/skill:setup-pstack`. The package exposes only `skills/`, not the dormant automation pack.

Read the [host contract](README.md). Use Pi's available `read`, `bash`, `edit`, and `write` tools for file work. Resolve all relative skill paths against the loaded skill's directory. Read sibling skills directly rather than sending slash commands to a shell.

Pi does not require a delegation extension. Inspect the current tools before using workers; do not assume `Task`, `spawn_agent`, background agents, or a particular extension exists. When no delegation tool exists, work sequentially and report independent-review gates as unmet. If an extension provides workers, follow its schema and pass the absolute contract, skill, and agent-brief paths to each worker. Do not start nested Pi processes to bypass missing capabilities.

Models inherit the session by default. Read `~/.config/pstack/models.md` when present. Setup uses the role labels from `setup-pstack`, with `inherit-parent` for scalar roles and two `inherit-parent` entries for panel roles. Confirm choices and write plain Markdown without frontmatter. Only offer model or effort overrides verified against the installed delegation tool; Pi's session model availability alone does not prove workers accept overrides. Report unsupported budget controls rather than changing Pi settings. Keep configuration outside the package so updates preserve it.

Use a checklist for plans and plain text for questions unless a tool provides those operations. Use a verified event watcher or bounded polling only while the session is active; checkpoint before stopping. No persistent wakes or cloud machines are implied.

Use `.agents/skills/` for generated project skills and `AGENTS.md` for project instructions. For history-based work use the current session context or an explicit workspace-matched session path from the host/user. Session directories are configurable; do not guess or scan all of `~/.pi`.

Run helper scripts with `--host portable` per the host contract. Forge operations use available repository tooling such as `gh`. Cursor automation provisioning remains unavailable unless the user explicitly supplies that integration. Never represent a sequential check as independent review.

If Pi already discovers the Codex install through `~/.agents/skills`, do not install a duplicate copy: that shared pack's host contract selects Pi at runtime, regardless of its installation path.
