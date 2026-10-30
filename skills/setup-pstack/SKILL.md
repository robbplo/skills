---
name: setup-pstack
description: Configure which models pstack uses per role and at what reasoning budget. Detects your available models and writes an always-applied rule that overrides the skill defaults. Use for /pstack:setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack

Write `~/.claude/rules/pstack-models.md` to set pstack's model per role. Claude Code loads this plain Markdown rule in new sessions. Do not put these role lines in `CLAUDE.md` or `AGENTS.md`.

## Steps

### 1. Detect available models

Inspect the `Agent` tool schema. The available `model` values are `opus`, `sonnet`, `haiku`, and `fable` when listed there. Pair each supported model with a supported `effort` value, written as `<model> <effort>`, such as `opus xhigh`. If no models can be detected, ask the user for their available choices. Never write an unverified model. `inherit-parent` and `auto` are always valid aliases.

### 2. Load current state

The defaults are the role lines in step 5. Read the current rule file if it exists; use its budget and role values as the current choices. Drop role lines no longer listed in step 5.

### 3. Budget, map, and confirm

**(a) Ask for a budget.** Prefer AskUserQuestion over free text. Offer these four options with these exact labels, and name the current budget when the rule records one. With no rule, say that `large` matches the skill defaults.

- `unlimited — max reasoning`
- `large — xhigh reasoning`
- `medium — high reasoning`
- `small — medium reasoning`

**(b) Apply it.** Keep changed roles on a re-run. The four budgets set each real model's effort to `max`, `xhigh`, `high`, or `medium`, respectively. Use the highest supported effort at or below the target. `inherit-parent` and `auto` stay unchanged.

**(c) Show the roles and confirm.** Show every role with its model, marking any real slug not in the detected set as needing a choice. Also list each line step 2 dropped. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` (both mean: this role runs on the parent chat model, which is how Auto users stay on Auto) as the options. Prefer AskUserQuestion over free text. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one value from it whose model family differs from the parent's when possible. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 4. Validate

Every real model and effort written must be in the detected set. `inherit-parent` and `auto` always pass. If a chosen model or effort is not available, stop and ask again.

### 5. Write the rule

Write `~/.claude/rules/pstack-models.md` as plain Markdown, without frontmatter. Include the comment lines, a `# budget` line, and one line per role. Overwrite the file so re-runs are idempotent.

```
# pstack model configuration. One line per role. Delete a line to fall back to the skill default.
# `inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit Agent `model`). Alias entries in a panel list still count toward its fan-out.
# budget: large (xhigh)
feature, refactoring: inherit-parent
bug-fix: inherit-parent
perf-issue: inherit-parent
hillclimb: inherit-parent
judgment and prose: opus xhigh
hardest tasks: opus xhigh
how explorer: inherit-parent
how explainer: opus xhigh
why investigators: inherit-parent
why synthesizer: opus xhigh
reflect tooling: inherit-parent
reflect judgment, divergent, synthesizer: opus xhigh
arena runners: opus xhigh, inherit-parent
arena cross-judge pool: opus xhigh, inherit-parent
swarm workers: inherit-parent
architect runners: opus xhigh, inherit-parent
interrogate reviewers: opus xhigh, inherit-parent
```

### 6. Confirm

Tell the user where the rule was written and that it applies to new sessions. Re-running this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /pstack:create-verification-skill." On yes, read `../create-verification-skill/SKILL.md` and follow it. On no, move on without pushing.

### 8. Offer a formal verification skill (optional)

Check whether the project already has a formal verification skill (a project skill that runs a model checker, a proof, or another verifier against the code). If not, offer once: "want a formal verification skill, so agents can prove a key property of your code holds in every case in scope, not only the cases tests reach? I can generate one with /pstack:create-formal-verification-skill." On yes, read `../create-formal-verification-skill/SKILL.md` and follow it. On no, move on without pushing.
