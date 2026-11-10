---
name: ship-pr
description: "Take a finished branch from code-complete to merged: sync with the base branch, review and fix, prove it in the running app, push, watch CI, merge on the user's word, then file open questions and deploy steps. Use for /ship-pr, or when the user says ship, land, get this merged, or merge the PR once CI passes."
disable-model-invocation: true
---

# Ship a PR

Run the steps in order. Skip a step only when its condition says so. Merging needs the user's word (step 7). Everything before it is yours to do without asking.

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

1. Run `/pstack:deslop` on the diff.
2. Run `/pstack:interrogate` on the diff against the docs or specs it implements.
3. Sort the findings into **act on** (wrong, or breaks a rule) and **consider** (judgment calls). Hand the act-on items and the cheap considers to one `pstack:poteto-agent` subagent to fix.
4. Ask the user about the remaining considers with `AskUserQuestion`, at most four per round. Don't ask about anything a test or a run can settle.

Skip this step when the diff is docs-only or under about 30 changed lines.

## 3. Docs follow the decisions

Write every answer the user gave in this session into the doc it decides, following the project's doc conventions. A decision that exists only in chat or a PR comment is lost on the next merge. When spec text changes, update the tests that pin it.

## 4. Prove it works

For a change a person can see, run the project's verify skill on the journey the change touches and link its evidence from the PR. Record the total run time and the slowest steps for the report. Evidence goes in the PR or an artifact, never in a commit.

Skip this step for API-only, tooling and docs changes, or when the project has no verify skill, and say that you skipped it. Offer `/pstack:create-verification-skill` when a visible change had nothing to run.

## 5. Push

Run the narrow tests you changed and the project's fast static checks, then push. When CI does the full run, don't repeat it locally. When the user says "just push", push without local checks.

## 6. PR and CI

1. Update the PR body to match the final diff, then mark the PR ready.
2. Watch CI with the host's PR watcher if it has one. Otherwise poll the checks with the forge CLI, such as `gh pr checks --watch`, during the active session.
3. On a red check, find the root cause before you change anything. If the base branch is red for the same reason, the fix is its own PR on the base. Never retry, skip or quarantine a test to get to green.
4. Stay quiet when a CI event changes nothing.

## 7. Merge

Merge only after the user says to: "merge it", "merge once CI passes", or a go-ahead given earlier in this session. Merge with the forge, such as `gh pr merge`, then read the PR back to confirm it shows as merged.

## 8. Close out

1. Post one PR comment that lists:
   - the open questions that still block parts of this change, each with the part it blocks
   - parts the coverage report shows as partly tested
   - manual production steps, such as migrations to apply, buckets or queues to create, and new environment keys
   - follow-ups found along the way
2. When anything in that comment needs someone else or later work, open an issue that holds the same list.
3. Stop any watcher or scheduled check-in you started.

## Report

Keep it short. Include the PR link, the merge state, the coverage change, the verify evidence link with its run time, and the open questions.
