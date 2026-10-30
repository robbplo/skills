# Set up pstack

Install for your agent, choose supported models, and run a first task. Cursor is not required.

## Install

| Agent | Install | Invoke |
|---|---|---|
| Claude Code | `/plugin marketplace add robbplo/skills`, then `/plugin install pstack@robbplo-skills` | `/pstack:poteto-mode <task>` |
| Codex | From this checkout: `python3 scripts/install-codex.py` | `$poteto-mode <task>` |
| Other agents | Make this checkout's `skills/` discoverable using the host's skill settings | Read `skills/poteto-mode/SKILL.md` directly |

Global compatibility instructions are a setup prerequisite, not a per-skill read. Codex's installer includes them. For Claude Code, use `--host claude-code` with its installed pack path. This embeds the full shared and selected host rules in the host's global instruction file. See the [README](../../README.md#global-instruction-setup-required) for defaults, safety checks, and updates. Restart or reload the agent afterward. Cursor users can still use the plugin and `/name` commands.

Throughout this guide, `/name` is shorthand for the active agent's invocation syntax, not a command to execute in a shell.

## Choose models

Invoke `setup-pstack` using your agent's syntax. It follows the already-loaded global compatibility rules, checks the available delegation controls, and confirms role choices before writing configuration:

- Codex: `<installed-pack>/models.md`.
- Claude Code: `~/.claude/rules/pstack-models.md`.
- Cursor: `~/.cursor/rules/pstack-models.mdc`.

Codex inherits the session model by default. Only configure model and reasoning overrides that the actual worker tool supports. A panel list sets the number of independent workers, not a promise of multiple model families. Without delegation, the agent can do separable work sequentially, but cannot claim independent review.

Re-run setup to change role choices. Setup offers once to generate a project verification skill and a formal verification skill if the project lacks them. Generated skills go into the active host's project skill directory (`.agents/skills/` for Codex, `.claude/skills/` for Claude Code). A verification skill must prove a real app journey before you rely on it.

## First task

For example, in Codex:

```text
$poteto-mode fix the settings form losing edits when I switch tabs. Reproduce it, fix the cause, and verify the real form.
```

In Claude Code use `/pstack:poteto-mode`. The skill selects a playbook and routes to the other skills as needed. Use it at the start of each new task; do not rely on a host-specific persistent mode.

If cost is a concern, use fewer panel seats or supported cheaper workers, and reserve full workflows for work that needs rigor. Unsupported controls are reported rather than emulated.

Next: [Give the agent a task](./02-poteto-mode.md).
