---
name: ship-pr
description: "Take a finished branch from code-complete to merged: sync with the base branch, review and fix, have an independent subagent prove it, push, watch CI, merge on the user's word, then file open questions and deploy steps. Use for /ship-pr, or when the user says ship, land, get this merged, or merge the PR once CI passes."
disable-model-invocation: true
---

# Ship a PR

Run the steps in order. Skip a step only when its condition says so. Merging needs the user's word (step 7). Everything before it is yours to do without asking.

Do every PR operation with the GitHub tools the session has, such as a GitHub MCP server or the host app's PR tools: reading the PR, its checks, review threads and comments, editing the body, commenting, merging and opening issues. Use the `gh` CLI only for an operation none of those tools offers, and say so in the report.

## 0. Read the project's shipping rules

Read the repository's agent instructions (`AGENTS.md`, `CLAUDE.md`, or the host's equivalent) and its contributing docs. Note, for the steps below:

- the code generation command to run after a merge, if any
- any check for IDs that parallel branches can reuse without a git conflict, such as numbered decision records, rule IDs, or migration versions
- where decisions and specs live, and how to edit them
- the project's verify skill, if it has one
- the fast local checks, and which CI job does the full run

When the project names none of these, skip the parts of the steps that need them and say so in the report.

## 1. Sync with the base branch

1. Fetch the base branch and merge it in, for example `git merge origin/main`. Never rebase or force-push a branch that has a PR.
2. Resolve conflicts by reading both sides against the project's docs. In the report, say what each side kept.
3. Run the project's code generation and commit any diff. Generated files come from the merged tree, never from either side.
4. Run the project's ID-collision check if it has one. Git merges two branches that add the same number with different meanings. Renumber on this branch, take the next free number on the base, and update every link to it. If another open branch collides with the base and not with you, report it rather than fixing it.

## 2. Review

1. Run `/pstack:deslop` on the code in the diff. Skip it when the diff has no code.
2. Run `/pstack:unslop` on the prose in the diff: docs, READMEs, skill text, the PR body and commit messages. Skip it when the diff has no prose.
3. Run `/pstack:no-comments` on the code in the diff. Skip it when the diff has no code.
4. Run `/pstack:interrogate` on the diff against the docs or specs it implements. Docs changes get this too. Interrogate them for wrong claims, contradictions with the code or other docs, and missing decisions.
5. Sort the findings into **act on** (wrong, or breaks a rule) and **consider** (judgment calls). Hand the act-on items and the cheap considers to one `pstack:poteto-agent` subagent to fix.
6. Ask the user about the remaining considers with `AskUserQuestion`, at most four per round. Don't ask about anything a test or a run can settle.

Skip this step only when the diff is code-only and under about 30 changed lines. A docs change always gets steps 2 and 3, however small.

## 3. Docs follow the decisions

Write every answer the user gave in this session into the doc it decides, following the project's doc conventions. A decision that exists only in chat or a PR comment is lost on the next merge. When spec text changes, update the tests that pin it.

## 4. Prove it works

Verification runs in a fresh subagent that wrote none of the code, because an author checks what it meant to build, not what it built. Spawn one `general-purpose` subagent at the committed head. Its brief names the head SHA, the user's goal, the diff, and what to prove:

- For a change a person can see, run the project's verify skill on the journey the change touches.
- For an API change, make real calls against a running server and compare the responses with the contract.
- For a tooling change, run the tool on a real input.
- For a docs or skill-text change, check each changed claim against the code or the files it names.

The verifier returns `PASS`, `PASS+NOTES` or `FAIL` for that SHA, with the commands it ran, their output, and the total run time with its slowest steps. It does not edit the branch. On `FAIL`, fix the cause and spawn a fresh verifier at the new head. Link the evidence from the PR. Evidence goes in the PR or an artifact, never in a commit.

When the project has no verify skill and the change is visible, the verifier still drives it by hand, and you offer `/pstack:create-verification-skill`.

## 5. Push

Run the narrow tests you changed and the project's fast static checks, then push. When CI does the full run, don't repeat it locally. When the user says "just push", push without local checks.

## 6. PR and CI

1. Update the PR body to match the final diff, then mark the PR ready.
2. Watch CI with the host's PR watcher if it has one. Otherwise poll the checks with the GitHub tools during the active session.
3. Read every review thread and bot comment. Triage each as fix, dismiss or ask, per `../poteto-mode/references/bugbot-triage.md`. Dismiss noise with a concrete reason in a reply on the thread.
4. On a red check, find the root cause before you change anything. If the base branch is red for the same reason, the fix is its own PR on the base. Never retry, skip or quarantine a test to get to green.
5. Stay quiet when a CI event changes nothing.

## 7. Merge

Merge only after the user says to: "merge it", "merge once CI passes", or a go-ahead given earlier in this session.

1. Read the PR's current head SHA. Merge only when the verifier's `PASS` or `PASS+NOTES` covers that SHA, CI is green there, and no review thread is unresolved. A push after the verdict needs a fresh verifier, unless it changes only wording.
2. Merge with the GitHub tools, pinned to that head SHA so a later push cannot land unverified. Use the repository's merge method, read from its settings or its recent merges, and pass it explicitly.
3. Read the PR back and confirm it shows as merged. A queued or auto-merge request is not a merge.

## 8. Close out

1. Post one PR comment that lists:
   - the open questions that still block parts of this change, each with the part it blocks
   - parts the coverage report shows as partly tested
   - manual production steps, such as migrations to apply, buckets or queues to create, and new environment keys
   - follow-ups found along the way
2. When anything in that comment needs someone else or later work, open an issue that holds the same list.
3. Stop any watcher or scheduled check-in you started.

## Report

Keep it short. Include the PR link, the merge state, the verifier's verdict and the SHA it covers, the coverage change, the verify evidence link with its run time, and the open questions.
