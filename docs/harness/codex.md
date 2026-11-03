# pstack in Codex (local install)

The source skills use Claude Code by default. The Codex installer adds a Codex
instruction to every installed skill before its body. Read this file once per
session, then use its mappings for Cursor and Claude Code instructions in the
skills. The host's tool schema and permissions take precedence.

Run `python3 scripts/install-codex.py` from this checkout. It copies the pack to
`~/.codex/pstack-local` and links its skills into `~/.agents/skills`. It refuses
to overwrite unrelated installations. Rerun after editing this checkout.
No marketplace, release, Claude installation, or global Codex config is changed.
The installer stages and validates the replacement before publication. It installs
`config/codex-models.md` as `models.md` (replacing any local edits to it), includes `README.md`, and
removes obsolete skill links only when they belong to this pack. Handled publication errors restore the previous pack
and links. The directory switch has a brief rename gap and is not atomic.
Rerun the installer to recover an interrupted switch from its managed backup.

Use `$poteto-mode <task>` or `$poteto-help` in Codex. Skills are
detected automatically; restart Codex if they do not appear. To uninstall, remove
only the symlinks pointing into `~/.codex/pstack-local/skills`, then that pack.

## Runtime adapter

Read this adapter before following any pstack skill. These mappings supersede
Cursor-specific instructions in the bundled skills, playbooks, and agent briefs.
`<pstack>` is the installed directory containing this file's `docs/` ancestor.
Never invent tool fields or claim an unavailable feature ran.

### Skills and tools

- `/name` and `/pstack:name` mean `$name` for user invocation. Strip the
  `pstack:` plugin prefix before resolving `<pstack>/skills/<name>/SKILL.md`
  and following it; no slash-command tool is needed.
- `Read`, `Grep`, `Glob`, and `Bash` mean the available Codex file/shell tools.
- `Task` and `Agent` mean `spawn_agent` when available. Use only fields accepted by the
  current schema. Track returned IDs with `wait`, `send_input`, and `close_agent`
  as available. Otherwise execute the steps sequentially and disclose that.
- Todo lists use `update_plan` when available, otherwise a checklist in replies.
- `AskQuestion` and `AskUserQuestion` mean `request_user_input` only when available in the current
  mode; otherwise ask in plain text. Do not enter plan mode just to ask.
- Cursor's built-in `create-skill` means Codex's `skill-creator` if available.
  Other unbundled skills are optional dependencies:
  report missing capabilities rather than pretending to invoke them.

### Wakes and autonomous work

Every reference to Cursor's `/loop` uses the available Codex event waits or
bounded polling during the active session. Read watcher output before the next
iteration. Use a watcher when the event can be observed directly. Otherwise
state the polling interval and exit predicate before polling. Do not invoke a
Cursor command or invent a scheduler.

Active-session polling cannot resume work after the turn ends or the app exits.
If the task requires a persistent wake and no verified mechanism is available,
record that limitation and save the checkpoint. Continue only work that does
not depend on that wake. Never report an hourly audit as armed merely because
its prompt was written.

### Plans and cleanup

Before copying the multi-phase plan skeleton, replace its trunk reads and wake
box with these Codex boxes. Resolve `<pstack>` to the absolute installed path
and fill the interval and predicate before handing over the plan.

```markdown
- [ ] Read installed playbooks. Read `<pstack>/skills/poteto-mode/playbooks/<execution playbook>.md` and every bundled leaf skill the plan uses at program start and each audit. List their absolute paths.
- [ ] Wake mechanism. Use the available event waits or poll every <interval> during the active session until <exit predicate> or an operator hold. Save a checkpoint if the session ends. Report each new tracked change in a status message.
```

Replace the audit prompt's instruction to read the playbook from trunk with an
instruction to read its installed absolute path. Replace other bundled `pstack/`
paths in the plan with installed absolute paths. The target project's code
still uses its own branches and commits. Do not use `git show` to read a pack
that is installed outside that repository. Validate the result with the
installed checker and the explicit host flag.

```bash
node "$HOME/.codex/pstack-local/skills/poteto-mode/scripts/check-plan.mjs" --host codex /absolute/path/to/plan.md
bash "$HOME/.codex/pstack-local/skills/poteto-mode/scripts/worktree-audit.sh" --host codex -b origin/main /absolute/path/to/repo
```

Use the actual installation path if `--home` changed it. The audit reports
`LAST_CHAT=unknown` and `BUCKET=verify-activity` for Codex unless a stronger hold
applies. It does not scan Cursor transcripts or infer that a worktree is idle.
Check active and pinned chats independently before pruning. An omitted host
also leaves activity unknown. Only `--host cursor` enables the Cursor scan.

Run these regression checks from the checkout before reinstalling.

```bash
python3 scripts/test_install_codex.py
python3 skills/poteto-mode/scripts/worktree-audit.test.py
bun test skills/poteto-mode/scripts/check-plan.test.ts
```

### Delegation

- `poteto-agent`, `comment-sicko`, `pstack:poteto-agent`, and
  `pstack:comment-sicko` are prompt briefs, NOT registered Codex
  agent types. Use an available agent type (normally `default`) and instruct
  it to read `<pstack>/agents/<name>.md` after stripping `pstack:`, this adapter, and the absolute
  `<pstack>/skills/poteto-mode/SKILL.md` path before working. Never search Cursor
  plugin directories. The parent owns the playbook and delegation.
- `generalPurpose`, `general-purpose`, and `Explore` mean an available general
  agent, normally `default`. `Explore` is read-only intent: instruct the worker
  not to edit files, then inspect the diff and status afterward.
- `readonly: true` means explicitly instruct the worker not to edit files,
  and inspect the diff/status afterward. This is not a sandbox guarantee.
- Drop `run_in_background`; use Codex's actual agent lifecycle. For `resume`,
  use supported agent messaging/resume tools, or start a new worker with a summary.
- Put file attachment paths in the brief. Do not pass Cursor-only fields.
- `environment: cloud` does not provision a cloud machine. When isolation is
  needed, create a local Git worktree from the requested base and give its
  absolute path to the worker. Otherwise report that cloud execution is absent.
  Do not let concurrent writers share files unintentionally.

### Models and setup

Claude/Grok slugs are not Codex model IDs. Do not translate them by
inventing names or silently assert a multi-model comparison happened. Panels
can use independent same-model workers; disclose the loss of model diversity.

Read `<pstack>/models.md` at the start of each pstack invocation. The installer
rewrites every reference to `config/claude-models.md` or `pstack-models.mdc` in
skill bodies to point at it; it is explicitly loaded, not an automatically
applied Codex rule.

Roles with no line in `models.md` inherit the session's model and reasoning
settings. Pass only the model and effort fields the delegation tool supports,
and never spawn nested CLI sessions to bypass this.

### Paths, unavailable features, and safety

- Skill discovery uses `~/.agents/skills` or project `.agents/skills`.
- Project instructions use `AGENTS.md`, not `.cursor/rules/*.mdc`. Do not modify
  global instructions or configuration merely to emulate always-applied rules.
- Resolve bundled docs locally under `<pstack>` instead of fetching GitHub copies.
- History-dependent skills must discover this workspace's Codex session records
  under `$CODEX_HOME/sessions` (default `~/.codex/sessions`), checking recorded
  workspace metadata. Never read Claude/Cursor history or unrelated workspaces.
  If records cannot be identified safely, ask for an explicit transcript.
- Cursor Automations, routine webhooks, cloud dashboards, and Bugbot provisioning
  are unavailable. State `Skipped in Codex: <step>. <reason>.` and proceed only
  where subsequent work does not depend on the missing result. Existing GitHub
  review comments can still be handled with `gh`; PR creation uses `gh pr create`.
- Autonomous playbooks do not override Codex permissions, sandboxing, or explicit
  user stop boundaries. Do not merge, publish, delete, or change production without
  the authorization required by the host and the user's request.

Reference: https://developers.openai.com/codex/skills/
