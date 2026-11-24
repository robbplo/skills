---
name: arena
description: "Spawn N parallel candidates at the same task, pick a base, graft the strongest parts of the losers into it. Use for /pstack:arena, 'arena this', 'throw it in the arena', or when one attempt at a non-trivial artifact would lock in the wrong shape."
argument-hint: "[task]"
---

# Arena

Open a todo list with one entry per phase (Frame, Fan out, Cross-judge, Pick, Graft, Verify) before launching anything.

## Phase A: Frame

Every candidate gets the same prompt, so the prompt is the contract.

1. State the artifact each candidate is producing.
2. Derive the rubric, 3-6 concrete gradeable criteria for what success looks like on *this* task. It is the picker's tool in Phase D. Candidates only see the task.
3. Pick the runners. Use the `arena runners` line in `../../config/claude-models.md`. If the file or that line is missing, default to one each on `opus xhigh` and `inherit-parent`. An `auto` or `inherit-parent` entry in this line means the parent model, so omit `model` for it. If the Agent tool rejects a configured model or effort, run that seat on its default and say so. If the Agent tool rejects that default too, drop the seat and say so. If dropped seats leave fewer than two runners, add runners until there are two, or one when the line has one entry. Run each added runner on a remaining runner's model, or omit `model` so it runs on the parent model when none remain, and say so. Spawn more runners when the arena covers multiple design directions. Use the same model N times when the work is generation-bound rather than judgment-sensitive. Pick each subagent's effort for the job, per the Subagents section of the **poteto-mode** skill.
4. Give each candidate its own output location (a git worktree where possible, otherwise `/tmp/arena-<slug>/candidate-<n>/`), per the **principle-separate-before-serializing-shared-state** skill.

## Phase B: Fan out

Run Phases B and C with the `Workflow` tool, running the `pstack:arena-run` workflow. If that name does not resolve, pass `scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/arena-run.js"`. Pass `args: {task, grounding, ref, rubric, candidates: [{label, model, effort, outputPath}], judge: {model, effort}}`. A worktree starts on the default branch, so set `ref` to the commit the candidates build on whenever that is not the default branch. Each candidate gets the task and the grounding, never the rubric, and works in its own git worktree unless you give it an `outputPath`. It reports where its artifact is and a rationale naming the alternatives it considered and what it rejected. Pick `judge` per Phase C, and leave it out when no pool entry qualifies. The workflow returns `{candidates, dropouts, verdict}`.

When the session has no `Workflow` tool, or the user declines the run, spawn all N subagents in one message with `Agent`, with the same task, grounding, output location, and report, then run Phase C by hand.

If a candidate is in `dropouts` or produced no output, proceed with N-1 and note the dropout.

## Phase C: Cross-judge

Choose one model from the `arena cross-judge pool` line in `../../config/claude-models.md`. If the file or that line is missing, choose from `opus xhigh` and `inherit-parent`. The judge is never on the parent's model. An `auto` or `inherit-parent` entry is the parent model, so it never judges. Claude Code offers only Claude models, so the judge cannot come from another family. Try the pool entries whose model differs from the parent's, in pool order, and say that the judge shares the parent's family. If the Agent tool rejects an entry, move to the next one. If no entry runs, or `verdict` comes back null, skip the judge, pick the base alone in Phase D, and say so. The workflow starts the judge as `Explore` once every candidate has finished. It sees the rubric and the candidates by label and location, scores each criterion from 1 to 5, and recommends a base with rationale. Check `git status` afterward. Without the workflow, spawn the same judge yourself, and never while candidates are still writing.

## Phase D: Pick a base

Read every candidate end to end before picking. Score each against the rubric criterion by criterion, not on holistic feel, and compare with the cross-judge when Phase C ran one. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous. Read both rationales before deciding.

Pick the base a future maintainer can extend most easily without breaking invariants. When two feel tied, prefer the cleaner boundary or smaller API, per the Laziness Protocol.

## Phase E: Graft

Walk each losing candidate once more for what is worth porting into the base, usually one or two things per candidate, not most of it. Fold each graft in by hand, per the **principle-redesign-from-first-principles** skill, so the result stays coherent under one mental model. Don't paste mechanically.

If the candidates converge on one shape, that is strong agreement. Note it and ship the consensus shape. No graft is needed. If they wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

Verify the synthesized artifact like any other output, per the **principle-prove-it-works** skill. If verification finds a problem the arena missed, either Phase A was wrong (re-frame and re-run) or a candidate caught it and you missed the graft (go back to Phase E). Don't paper over it.

## Outputs

One synthesized artifact, with a short synthesis note alongside naming the base and why, the cross-judge's verdict or that Phase C skipped the judge, each graft with its source candidate, what was rejected and why, any convergence or dropouts, and the verification result.
