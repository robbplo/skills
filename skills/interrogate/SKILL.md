---
name: interrogate
description: "Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"find blind spots\", or \"tear this apart\". Adversaries try to break a change or design, and only findings proven by a run survive."
argument-hint: "[diff, PR, or design to break]"
---

# Interrogate

Adversaries try to break a change or a design. A finding survives only when a run proves it. Report the findings. Do not apply fixes.

## Frame

The scope is what the user names. Otherwise it is the branch diff from its merge base with the base branch, through the working tree. State the intent with the **in-your-own-words** skill, from the user's message, the commits, and the PR description. Ask the user when the intent is unclear.

## Fan out and verify

Pick the adversaries per Phase A step 3 of the **arena** skill, reading the `interrogate reviewers` line in place of `arena runners`. When the scope has uncommitted changes, write them to a patch file with `git diff HEAD` and note its absolute path.

Run the adversaries with the `Workflow` tool, running the `pstack:interrogate-run` workflow. If that name does not resolve, pass `scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/interrogate-run.js"`. Pass `args: {scope, intent, ref, patchPath, adversaries: [{label, model, effort}]}`. A worktree starts on the default branch, so set `ref` to the commit under review whenever the scope is not on that branch. Each adversary works in its own worktree with the brief below. A fresh agent then reruns every finding's command in that worktree, and a finding survives only when the rerun shows the failure and the failure breaks the intent. The workflow returns `{findings, dropped, gaps}`.

When the session has no `Workflow` tool, or the user declines the run, run Phase B of the **arena** skill with `subagent_type: "general-purpose"`, copy the uncommitted changes into each worktree, give each adversary the scope, the intent, and this brief, wait for every result, and rerun each finding's command yourself:

> Break this change. Prove each finding with a run against the real code, such as a failing test, a repro script, or command output that shows the wrong behavior. For a design or plan, run a prototype or probe the current tree. Keep repros in your own worktree. Report each finding with a title, the exact command, the output it printed, and the output the intent requires. Leave out anything you did not run. That covers style, naming, structure, and risks that need a future change to matter. No findings is a valid result.

Merge the surviving findings that share a root cause. Adversaries find different failures, so the verdict keeps every verified finding, not one adversary's list. Arena's cross-judge, base pick, and graft do not apply.

## Output

- **Intent**: the restatement.
- **Findings**: for each verified finding, the command, its output, how it breaks the intent, and the adversaries that found it. Say "no verified findings" when none survive.
- **Dropped**: for each adversary, the count of dropped findings and why.

## Post to the PR

After you share the report in chat, check whether the current branch has an open PR (`gh pr view --json number,url`). If one exists, post the report to it as a comment, verbatim: the exact Markdown shared in chat, with no edits, trimming, or added preamble. Write it to a temp file and use `gh pr comment <number> --body-file <file>` so formatting survives. If there is no PR or `gh` is unavailable, skip this step and say so in one line. Never post anywhere else, and never post partial or draft output.
