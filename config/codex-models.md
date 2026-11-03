# pstack per-role model configuration

This file overrides pstack's bundled role defaults in Codex. Load it at the start
of each pstack invocation, as required by the Codex host adapter at
`<pstack>/docs/harness/codex.md`.

## Delegation settings

- Set `reasoning_effort: "high"` for every configured role and every panel entry.
  Pass the model ID and reasoning effort as separate supported tool fields;
  do not append an effort suffix to a model ID.
- For the `spawn_agent` API, explicit model or effort overrides require
  `fork_turns: "none"`. Provide a self-contained task brief, relevant context and
  file paths, and the absolute Codex adapter path to each delegate. On other
  hosts, use only the actual delegation API's supported fields.
- Panel lists create one independent worker per entry. The cross-judge pool is
  a selection pool, not a worker count; prefer a different model from the work
  being judged when possible. All configured models are OpenAI models; these
  settings do not provide cross-provider diversity.
- Missing roles inherit the parent session settings. A deliberate
  `inherit-parent` or `auto` role value inherits both model and reasoning;
  omit the corresponding overrides for those aliases.

## Role mapping

feature, refactoring: gpt-6.1-sol
bug-fix: gpt-6.1-sol
perf-issue: gpt-6.1-sol
hillclimb: gpt-6.1-sol
judgment and prose: gpt-6.1-sol
hardest tasks: gpt-6.1-sol
how explorer: gpt-6-luna
how explainer: gpt-6.1-terra
why investigators: gpt-6.1-sol
why synthesizer: gpt-6.1-sol
reflect tooling: gpt-6.1-sol
reflect judgment, divergent, synthesizer: gpt-6.1-sol
arena runners: gpt-6.1-terra, gpt-6.1-sol
arena cross-judge pool: gpt-6.1-terra, gpt-6.1-sol
swarm workers: gpt-6.1-sol
architect runners: gpt-6.1-terra, gpt-6.1-sol
interrogate reviewers: gpt-6.1-sol, gpt-6.1-terra

## Selection rationale

- Sol handles implementation, refactoring, debugging, performance, optimization,
  difficult changes, judgment, prose, synthesis, tooling, and swarm work.
- Terra handles clear explanations and joins Sol on review, arena, and
  architecture panels.
- Luna handles focused factual reconnaissance for the how explorer. Assign
  open-ended investigation or difficult code reasoning to Sol.
- The cross-judge pool lists each available model once.
