# pstack in Claude Code

pstack skills use Claude Code names by default, but some bundled playbooks and references still use Cursor names. Read this file once per session before running `poteto-mode` and apply its mappings to those files. `<pstack>` means the folder that holds `skills/` and `docs/`. If a Cursor field has no row, drop it and say so. Never pass a field or value the tool schema rejects.

## Tools

| Cursor | Claude Code |
| --- | --- |
| `Task` | `Agent` |
| `AskQuestion` | `AskUserQuestion`. In `-p` mode it is absent, so ask in plain text. |
| Open a todolist | Use `TodoWrite` if the session offers it. Otherwise keep the list in your reply and update it at each phase. |
| Run another pstack skill (`/name`, `/pstack:name`, or "the **name** skill") | Strip `pstack:` from the name, then `Read` `<pstack>/skills/<name>/SKILL.md` and follow it. The `Skill` tool refuses most pstack skills. When you tell the user to type it, write `/pstack:<name>`. |
| `Grep`, `Glob` | `Bash` with `rg` when the session has no `Grep` or `Glob`. |

## Subagent fields

| Cursor | Claude Code |
| --- | --- |
| `subagent_type: generalPurpose` | `subagent_type: "general-purpose"` |
| `poteto-agent`, `comment-sicko` | `pstack:poteto-agent`, `pstack:comment-sicko` |
| `readonly: true` | `subagent_type: "Explore"`. It keeps `Bash`, so the brief also says "do not edit files", and you check `git status` afterward. |
| `readonly: false` | `general-purpose`. It keeps the session's MCP servers. |
| `environment: "cloud"` | `isolation: "worktree"`. Name the branch or commit the worker checks out. |
| `environment: "local"` | Omit. |
| `cloud_base_branch: <b>` | Tell the worker to check out `<b>` first. |
| `run_in_background: true` | Omit. Subagents run in the background by default and notify you when they finish. |
| `resume` | Spawn a new agent and paste the earlier result into its brief. |
| `file_attachments` | List the paths in the brief. |

## Models

| Cursor | Claude Code |
| --- | --- |
| `claude-<family>-<version>-<effort>[-fast]`, such as `claude-opus-5-5-xhigh` | `model: "opus"` and `effort: "xhigh"`. `model` takes only `opus`, `sonnet`, `haiku`, `fable`. Drop `-fast`. |
| A `grok-*`, `gpt-*`, or other non-Claude slug | Omit `model` so the agent runs on the session model, and say so. |
| `auto` or `inherit-parent` | Omit `model`. |
| The `pstack-models.mdc` rule, `~/.cursor/rules/pstack-models.mdc` | `config/claude-models.md`. Skills read it by relative path when they name a role line. If the file or the role's line is missing, use the skill's default slug. |
| A role value `<model> <effort>`, such as `opus high` | `model: "opus"` and `effort: "high"`. |

## Paths

| Cursor | Claude Code |
| --- | --- |
| `.cursor/skills/`, `~/.cursor/skills/` | `.claude/skills/`, `~/.claude/skills/` |
| `~/.cursor/plugins/`, `.cursor-plugin/plugin.json` | `~/.claude/plugins/`, `.claude-plugin/plugin.json` |
| `.cursor/rules/*.mdc`, always-applied rules | `CLAUDE.md`, or `AGENTS.md` when no `CLAUDE.md` exists. Claude Code never reads `.mdc` files. The model rule is the exception. See Models. |
| `https://github.com/cursor/plugins/blob/main/pstack/<path>` | `<pstack>/<path>` when that file exists. The plugin ships the skills, `docs/guide/`, and `README.md`. Read the local copy and never fetch it. Give the user the URL when they need a link. |
| Transcripts in `~/.cursor/projects/<slug>/agent-transcripts/` | `~/.claude/projects/<slug>/<session>.jsonl`. The slug is the workspace path with each `/` and `.` changed to `-`, so `/Users/you/proj` is `-Users-you-proj`. Identify this session by ID or its user-message records; modification time alone does not identify it. Its `<session>/subagents/` folder holds subagent transcripts. Read only this workspace's folder. |

## Playbooks and plans

When a playbook says `Task`, use `Agent` and the subagent mappings above. Treat a Cursor cloud worker or verifier as a Claude Code agent with `isolation: "worktree"` when the task only needs an isolated checkout. Give it the base ref and repository path, and verify its branch, diff, and artifacts. A worktree is not a remote machine. If a step requires a cloud dashboard, persistent remote process, or an independent computer that this session cannot provide, report that prerequisite and stop the dependent step. Do not invent a verdict or advance a merge gate.

For an active-session wake, use an available event wait or poll at a stated interval until a stated exit predicate or operator hold. Save a checkpoint when the session ends. Do not claim that a written `/loop` prompt will wake Claude Code after the session ends. Replace other Cursor-only commands in a playbook using this adapter before executing them.

Before copying the multi-phase plan skeleton, replace its bundled-source reads and `/loop` box with these Claude Code boxes. Resolve `<pstack>` to the absolute installed plugin path and fill in the interval and exit predicate:

```markdown
- [ ] Read installed playbooks. Read `<pstack>/skills/poteto-mode/playbooks/<execution playbook>.md` and every bundled leaf skill the plan uses at program start and each audit. List their absolute paths.
- [ ] Wake mechanism. Use an available event wait or poll every <interval> during the active session until <exit predicate> or an operator hold. Save a checkpoint if the session ends. Report each new tracked change in a status message.
```

Replace the audit prompt's trunk read with a read of the installed absolute playbook path. Replace other bundled `pstack/` paths with installed absolute paths; the target project's code still uses its own branches and commits. Do not copy the skeleton's claim that every live lane has its own cloud VM unless that is true of the actual environment. Validate the resulting plan with `node <pstack>/skills/poteto-mode/scripts/check-plan.mjs --host claude <plan.md>`. For worktree cleanup, use `worktree-audit.sh --host claude -b <base> <repo>`; its chat-activity column is unknown, so verify activity before pruning.

## Cursor-only features

Claude Code has no Cursor Automations, Bugbot, Cursor cloud agents, or built-in PR tool. When a step needs one, put one line in your reply, `Skipped in Claude Code: <step>. <reason>.`, then go on to independent work. Stop dependent work when it needs what the skipped step would have produced, such as a URL, key, or independent verdict.

| Cursor | Claude Code |
| --- | --- |
| Cursor Automations: routines, `update_state` routine calls, `api2.cursor.sh/automations` webhooks, routine wakes, and `SendToUser` secret requests | Skip with the line. |
| Bugbot | Bugbot comments on a GitHub PR are ordinary review threads, so triage them with the forge command that the step gives. Skip a step that starts, waits for, or configures Bugbot when the PR has no Bugbot check or comment. |
| Cursor cloud agents | `environment: "cloud"` maps to a worktree, as in Subagent fields. Skip a step that needs the cloud agent itself, such as its dashboard status or its own machine. |
| A built-in PR tool | Use the forge command that the step gives, such as `gh pr create`. That is not a skip, so write no line. |
