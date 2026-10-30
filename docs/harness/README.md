# Host contract

Read this before executing a pstack skill or agent brief. It applies to every nested playbook and reference. Host tool schemas, permissions, and user boundaries always win. This contract overrides host-specific examples in skill bodies; the selected adapter supplies concrete mappings, not extra capabilities.

## Select the active host

- **Codex:** [Codex adapter](codex.md).
- **Pi:** [Pi adapter](pi.md).
- **Claude Code:** [Claude Code adapter](claude-code.md).
- **Cursor:** Cursor examples may be used only when the named capability exists.
- **Other hosts:** use the capability rules below. Do not guess a host from the model provider or the presence of another agent's files.

Resolve bundled files relative to this installation, never the target repository or a marketplace cache guessed from its name. `/name` in prose means read `skills/<name>/SKILL.md` and follow it. User command syntax depends on the host. Pass this contract and the installed brief paths to delegates.

## Capabilities, not tool names

- `Read`, `Grep`, `Glob`, `Bash`, `Task`, `TodoWrite`, and `AskQuestion` describe operations. Use available file, search, shell, delegation, planning, and question tools with their actual schemas. A plain checklist or question is sufficient when no dedicated tool exists.
- Delegation is optional. Use independent workers when supported; otherwise do separable work sequentially and disclose the fallback. Sequential self-review is not an independent review, a multi-model panel, or a race. If independence is a release gate, report it unmet rather than claiming PASS.
- Agent names in `agents/` are briefs unless registered by the host. Background, resume, readonly, attachment, effort, and cloud fields are not portable. Do not pass unsupported fields. A readonly instruction is not a sandbox. A local worktree isolates files, not a machine.
- Inherit the session model by default, including missing role lines. Use only verified model identifiers and effort controls accepted by the delegation tool. Never translate provider slugs by guessing. Preserve panel seat counts, but disclose unavailable model diversity. Cursor's model defaults apply only in Cursor; other adapters may supply verified host defaults.
- Read the active adapter's model file explicitly when needed. For an unlisted host use `~/.config/pstack/models.md`, plain Markdown. Setup preserves role labels, confirms choices, and writes only supported settings. It must not alter global host configuration to imitate always-applied rules.
- Generated project skills belong in `.agents/skills/` for Codex, Pi, and generic hosts, `.claude/skills/` for Claude Code, or `.cursor/skills/` for Cursor. Preserve existing project conventions when explicitly configured. Project instructions use the host's supported instruction file, not automatically `.mdc` rules.
- `create-skill` means the host's skill-authoring helper if present. Otherwise author a directory with `SKILL.md`, valid `name` and `description` frontmatter, checked relative links, and tested helpers. No built-in authoring command is required.
- `/loop` means a verified watcher or bounded active-session polling. State interval, exit predicate, and deadline. Save a checkpoint when the session ends. Do not claim persistent scheduling, cloud execution, or completion from a written prompt.
- History access is confined to records whose metadata identifies the active workspace. Never search another host's history or unrelated workspaces. Ask for a transcript when safe discovery is unavailable.
- Cursor Automations and cloud dashboards are optional integrations, not prerequisites. Report unavailable steps and continue only independent work. Stop dependent work with the missing prerequisite; do not fabricate URLs, secrets, reviews, or evidence. Existing review comments, including Bugbot comments, can be handled through the repository's forge tools.
- Publishing, merging, deleting, provisioning automations, and production changes still require the authorization applicable to the user's request. A playbook never overrides a stop boundary.

## Helper scripts

For portable plan validation use `check-plan.mjs --host portable`; replace trunk reads of bundled files with their installed absolute paths and use an active-session wake/checkpoint box as described in the Codex adapter. Worktree auditing uses `worktree-audit.sh --host portable` and leaves activity unknown. Verify activity independently before deletion. Only explicit `--host cursor` may read Cursor transcripts.
