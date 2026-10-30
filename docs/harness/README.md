# Shared pstack compatibility rules

Before using pstack, install these shared rules and the selected host's rules in its always-loaded global instruction file with `scripts/install-instructions.py`. Skills and agent briefs assume setup is complete. They do not reload compatibility documents.

<!-- pstack:runtime -->

## Shared compatibility rules

These rules apply to every nested playbook and reference. Host tool schemas, permissions, and user boundaries always win. The installed rules override host-specific examples in skill bodies. Mappings do not grant extra capabilities.

Resolve bundled files under `<pstack>`, never the target repository or a marketplace cache guessed from its name. `/name` in prose means read `<pstack>/skills/<name>/SKILL.md` and follow it. User command syntax depends on the host. Give delegates the applicable loaded rules as content or an absolute path to the global instruction file. Include the installed brief paths. Do not assume subagents inherit global instructions. Do not guess a host from the model provider or the presence of another agent's files.

## Capabilities, not tool names

- `Read`, `Grep`, `Glob`, `Bash`, `Task`, `TodoWrite`, and `AskQuestion` describe operations. Use available file, search, shell, delegation, planning, and question tools with their actual schemas. A plain checklist or question is sufficient when no dedicated tool exists.
- Delegation is optional. Use independent workers when supported. Otherwise, do separable work sequentially and disclose the fallback. Sequential self-review is not an independent review, a multi-model panel, or a race. If independence is a release gate, report it unmet rather than claiming PASS.
- Agent names in `agents/` are briefs unless registered by the host. Background, resume, readonly, attachment, effort, and cloud fields are not portable. Do not pass unsupported fields. A readonly instruction is not a sandbox. A local worktree isolates files, not a machine.
- Inherit the session model by default, including missing role lines. Use only verified model IDs and effort controls that the delegation tool accepts. Never translate provider slugs by guessing. Preserve panel seat counts, but disclose unavailable model diversity. Cursor's model defaults apply only in Cursor; other adapters may supply verified host defaults.
- When needed, read the model file that the loaded host rules specify. For an unlisted host, use `~/.config/pstack/models.md` in plain Markdown. Setup preserves role labels, confirms choices, and writes only supported settings. It must not alter global host configuration to imitate always-applied rules.
- Generated project skills belong in `<project-skills>`. Preserve existing project conventions when explicitly configured. Project instructions use the host's supported instruction file, not automatically `.mdc` rules.
- `create-skill` means the host's skill-authoring helper if present. Otherwise author a directory with `SKILL.md`, valid `name` and `description` frontmatter, checked relative links, and tested helpers. No built-in authoring command is required.
- `/loop` means a verified watcher or bounded polling during the active session. State the interval, stop condition, and deadline. Save a checkpoint when the session ends. Do not claim persistent scheduling, cloud execution, or completion from a written prompt.
- Read only history records whose metadata identifies the active workspace. Never search another host's history or unrelated workspaces. Ask for a transcript when safe discovery is unavailable.
- Cursor Automations and cloud dashboards are optional integrations, not prerequisites. Report unavailable steps and continue only independent work. Stop dependent work and report the missing prerequisite. Do not fabricate URLs, secrets, reviews, or evidence. Use the repository's forge tools to handle existing review comments, including Bugbot comments.
- Publishing, merging, deleting, provisioning automations, and production changes still require the authorization applicable to the user's request. A playbook never overrides a stop boundary.

## Helper scripts

To validate portable plans, use `check-plan.mjs --host portable`. Replace trunk reads of bundled files with their installed absolute paths. Use an active-session wake/checkpoint box with an interval, stop condition, and deadline. Audit worktrees with `worktree-audit.sh --host portable`, which leaves activity unknown. Verify activity independently before deletion. Only explicit `--host cursor` may read Cursor transcripts.
