---
name: submit-pr
description: Open a pull request, then watch its CI and handle failures. Use whenever the user asks to create or open a PR, or to submit, ship, or send up their work.
---

# Submit a PR

Open the PR the normal way, then follow it until CI settles. Passing CI ends the job. Failing CI needs a decision.

## Open

1. Branch off trunk if you are on it. Commit the work in small, ordered commits. Titles follow Conventional Commits `type(scope): subject`.
2. Push with `-u`.
3. Write the description from the full branch diff against trunk (`git diff <base>...HEAD`), not the last commit. Say why the change exists, what it leaves out, and how you verified it.
4. Create it ready for review, never as a draft. Use the built-in PR tool when the run has one. Otherwise use `gh pr create`.
5. Post the PR URL.

## Subscribe

Right after the PR exists:

- With the ccd_pr tools: call `get_status`. If it does not report this PR, call `bind_pr`. Then read CI and offer Auto-fix. Do not poll or schedule your own checks.
- Without them: `gh pr checks <number> --watch`, run in the background.

Never enable auto-merge unless the user asked.

## When CI finishes

**Passes:** report the PR URL and that checks are green. Stop.

**Fails:** read the failing job logs first (`gh run view <run-id> --log-failed`). Do not guess from the check name. Then decide whether to fix it.

Fix it when the failure is in this branch's own change and a small, clear edit resolves it:

- a broken or outdated test for code you changed
- a lint, format, type, or build error in the diff
- a missing file, snapshot, or generated artifact the change needs

Do not fix it when the fix is not yours to make or would not be honest:

- the same check fails on trunk, so the failure predates the branch
- a flaky or infra failure (timeout, runner error, network, rate limit). Re-run once at most, then report.
- the fix needs a secret, permission, or setting you do not have
- the only way to go green is to weaken the check: deleting or skipping a test, loosening an assertion, adding a lint ignore
- the fix is a design change the user should make, or reaches well outside the PR's scope

**If you fix it:** make the change, commit, push, and go back to **Subscribe** for the new run. Repeat. After three failed attempts on the same failure, stop and treat it as a "do not fix".

**If you do not fix it:** leave the PR as is and tell the user, in plain words:

- which check failed and the line of the log that shows why
- which reason above applies, and why that means you should not fix it
- what they would need to do, or decide, next
