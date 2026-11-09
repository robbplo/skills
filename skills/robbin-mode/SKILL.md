---
name: robbin-mode
description: "Robbin's working style, layered on poteto-mode. Use for /robbin-mode, or when asked to work like Robbin or in their style."
disable-model-invocation: true
---

# Robbin mode

Read the **poteto-mode** skill (`../poteto-mode/SKILL.md` from this file) in full and follow it. The rules below add to it or override it. The repository's own agent instructions win over both.

## Replies

- The user writes short, lowercase messages and answers with the next action. Lead with the outcome and what needs them. Put details below it.
- Report durations whenever you run something slow: the verification, the test suite, CI. Give the wall time and the slowest step.
- When a CI or PR event changes nothing, say nothing.

## Scope

- When you find a problem outside the task, queue it as a separate task or session with a complete brief: goal, files, cause and "done when". Don't widen the current PR.
- Prefer the simplest fix, such as pinning, deleting or a default, over new machinery. Before you build a workaround, ask whether a one-line change removes the need for it.

## Review findings

Sort findings into **act on** and **consider**. Fix the act-on items and the cheap considers without asking. Interview the user about the rest, a few questions per round.

## Git

- Merge the base branch in, and never rebase or force-push a branch that has a PR. Run the project's code generation after every merge.
- Parallel branches can collide on numbered IDs, such as decision records or migration versions, without a git conflict. When the project has a check for this, run it before you push a change that adds one.
- Push and let CI do the full run. Locally, run only the narrow tests and the fast static checks.

## Done

- A user-facing change is done once the project's verify evidence is linked from the PR. Passing tests alone don't count.
- A decision the user made in chat goes into the project's docs before the merge.
- To land a PR, follow the **ship-pr** skill (`../ship-pr/SKILL.md`). Merge only on the user's word.

## Environment

If a service the session needs is down at the start, such as a database or container runtime, a setup hook probably failed. Start it as the project's verify skill does, then report the failure as a separate task. Don't fix it silently in each session.
