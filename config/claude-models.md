# pstack model configuration. One line per role. Delete a line to fall back to the skill default.
# `inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit the `Agent` `model`). Alias entries in a panel list still count toward its fan-out.
# A bare model leaves effort to the skill, which picks it per subagent. Write `<model> <effort>`, such as `opus high`, to fix it.
feature, refactoring: sonnet
bug-fix: sonnet
perf-issue: sonnet
hillclimb: sonnet
judgment and prose: opus
hardest tasks: opus
mechanical and clerical: sonnet
how explorer: sonnet
how explainer: opus
why investigators: sonnet
why synthesizer: opus
reflect tooling: sonnet
reflect judgment, divergent, synthesizer: opus
arena runners: opus, sonnet
arena cross-judge pool: opus, sonnet
swarm workers: sonnet
architect runners: opus, sonnet
interrogate reviewers: opus, sonnet
