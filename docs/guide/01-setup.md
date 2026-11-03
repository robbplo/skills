# Set up pstack

In this page you install the plugin, pick which models pstack uses, and run your first task. Setup is one command plus a short conversation.

## Install the plugin

In a Cursor chat, run:

```text
/add-plugin pstack
```

Cursor confirms the plugin is installed.

In Claude Code, run `/plugin marketplace add robbplo/skills`, then `/plugin install pstack@robbplo-skills`. Claude Code prefixes plugin commands, so each command in this guide takes a `pstack:` prefix there, such as `/pstack:poteto-mode`. The [Claude Code adapter](../harness/claude-code.md) covers the other differences.

## Pick your models

Cursor reads the Claude file. The model choices live in [`config/claude-models.md`](../../config/claude-models.md) (Claude Code) and [`config/codex-models.md`](../../config/codex-models.md) (Codex). To change them, fork the repo, edit the file, and install your fork. Edits inside an installed plugin copy are lost on update. The files are plain Markdown with one line per role (code delegates, judgment, the review panels).

You only override what you care about. A role with no line keeps the skill's default. To restore a default, delete that role's line.

You might be wondering what happens if you use Auto. Set a role to `inherit-parent` or `auto` and pstack omits the subagent `model` field, so the subagent inherits your parent chat model. Both values mean the same thing, and neither is a model slug. For a panel role the value is a list, and one subagent runs per entry, so the list length sets the panel size. `swarm workers` is the default model for every `/swarm` worker unless a race names a model for each arm.

## Add a verification skill

If your project has no `verify-*` skill or other harness that proves app behavior, generate one with [`/create-verification-skill`](../../skills/create-verification-skill/SKILL.md). It writes `.claude/skills/verify-<app>/` (`.cursor/skills/verify-<app>/` in Cursor), a project-local skill that teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers it in depth.

If you're new to pstack, do this. An agent that can check its own work keeps going until the check passes. An agent that can't hands every result back to you to check by hand.

Then consider a formal verification skill with [`/create-formal-verification-skill`](../../skills/create-formal-verification-skill/SKILL.md). Tests check the cases someone thought to write. A formal verification skill checks one key property of your code, such as "a job never runs twice at once", in every case within a stated scope. Worth it when your code has concurrency, retries, a state machine, or a parser, where a bug is costly and tests rarely reach the case that breaks. [Verify and ship](./06-verify-and-ship.md#prove-a-property-with-a-formal-verification-skill) covers it.

After editing the model files, start a new chat.

## Keep the cost in check

pstack spends extra tokens on subagents and review panels. That's the price of the rigor. To spend fewer:

- Pick cheaper models in the config files. A strong model in the main chat with cheaper, faster models in the code roles is a good split.
- Set a role to `auto` or `inherit-parent` so it runs on the chat's own model.
- Shorten a panel list. Each entry runs one subagent.
- Save `/poteto-mode` for work that needs rigor. A small, obvious edit doesn't.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt. If `/poteto-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.

From here you can type normal follow-ups. To keep `/poteto-mode` on for the whole chat, pick it from the `/` menu with Option+Enter (Mac) or Alt+Enter (Windows) instead of Enter. That makes it a [Custom Mode](https://cursor.com/docs/skills#using-a-skill-as-a-custom-mode), which stays in context on every turn until you exit it. Custom Modes are available in the Agents Window and the CLI. Plain Enter attaches the skill to one message, and it fades as the chat moves on.

Next: [Route work through `/poteto-mode`](./02-poteto-mode.md).
