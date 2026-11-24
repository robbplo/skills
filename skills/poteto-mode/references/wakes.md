# Wakes

Pick the row that matches what you wait for. State the mechanism, the interval or deadline, and the exit predicate before you arm it.

| You wait for | Use | Outlives the session |
| --- | --- | --- |
| A delegate's result | A background `Agent` call. Its completion wakes you. | No |
| A command that ends, such as a test run, a build, or `gh pr checks --watch` | `Bash` with `run_in_background`. Its exit wakes you. | No |
| Lines from a command that keeps running, such as a log tail or `scripts/watch-pr/watch-pr` | `Monitor`. Each line wakes you. A monitor lasts 30 minutes at most, so re-arm it. | No |
| A check on a cadence you pick | The `/loop` skill with no interval. It paces itself from 1 minute to 1 hour. | No |
| A check at a fixed time or interval | `/loop <interval>`, or `CronCreate` for a clock time. | No |
| Work that must go on with the laptop closed | The `/schedule` skill. It runs a cloud agent from a fresh clone on a schedule. | Yes |

An event beats a poll. Poll only when nothing emits the event.

A `/schedule` agent sees only what is pushed. Before you arm one, push the branch and write the checkpoint where a fresh clone finds it, in the PR or a committed trail. Its prompt names the repository, the branch, the exit predicate, and the playbook to re-read. A schedule is standing configuration, so arm it only on the operator's word or under a grant that covers it, and delete it when the predicate passes.

Every other row dies with the session. Save a checkpoint per `playbooks/pause-safely.md` when the session ends, and never claim a wake that outlives it.
