---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /pstack:swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
---

# Swarm

## Start

Open a todo list with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Pick the worker model from the `swarm workers` line in `../../config/claude-models.md`. If the file or that line is missing, use `inherit-parent`. For `auto` or `inherit-parent`, omit `model` so the workers run on the parent model. If the Agent tool rejects a configured model or effort, use the role default and say so. For a model race, name each arm's model up front. Pick each subagent's effort for the job, per the Subagents section of the **poteto-mode** skill.
4. Give each worker its own writable output when it writes. When workers verify or measure commits, each brief names the exact SHAs. A measurement brief also names the method (sample count, what one sample is, order). The worker records both in its result.

## Phase B: Fan out

Fan out with the `Workflow` tool, running the `pstack:swarm-run` workflow. If that name does not resolve, pass `scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/swarm-run.js"`. Pass `args: {briefs: [{label, prompt, model, effort, isolation, mustRecord}]}`, one brief per worker. Give each brief `isolation: "worktree"` and the step 3 model, left unset for `auto` or `inherit-parent`. Omit isolation when the worker needs access to something on the user's computer. Put the exact SHAs and the method name a brief requires in its `mustRecord` list.

The workflow makes every worker report `PASS`, `ISSUES`, or `BLOCKED` with evidence. It respawns once any worker that returns nothing or leaves out a `mustRecord` entry, and returns `{results, gaps}`.

When the session has no `Workflow` tool, or the user declines the run, spawn all N workers in one message with `Agent`, `subagent_type: "general-purpose"`, and the same fields. Then respawn once, by hand, any worker whose result lacks the SHAs and method its brief names.

When a worker must start from a non-default pushed branch, name the branch or commit to check out in its brief.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence. A worker that can prove a defect reports `ISSUES` and lists every issue it can prove, not only the first.

A worker in `gaps` missed twice. Proceed with N-1 and note it.

## Phase C: Aggregate

Read the results. A gap does not count as a pass. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

## Phase D: Report

Return one consolidated in-chat report with a result table, issue one-liners, gaps or dropouts, and the race rule when used.
