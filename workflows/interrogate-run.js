export const meta = {
  name: 'interrogate-run',
  description: 'Run adversaries that try to break a change, then rerun every finding in a fresh agent and keep only the ones that reproduce',
  whenToUse: 'The Fan out and Verify sections of the pstack interrogate skill',
  phases: [
    { title: 'Break', detail: 'one adversary per reviewer, each in its own worktree' },
    { title: 'Verify', detail: 'one fresh agent reruns each finding' },
  ],
}

const input = typeof args === 'string' ? JSON.parse(args) : args
const { scope, intent, patchPath, adversaries } = input || {}
if (typeof scope !== 'string' || typeof intent !== 'string' || !Array.isArray(adversaries) || adversaries.length === 0) {
  throw new Error('interrogate-run needs args {scope, intent, adversaries: [{label?, model?, effort?}], patchPath?}')
}

const FINDINGS = {
  type: 'object',
  properties: {
    worktree: { type: 'string', description: 'Absolute path of the checkout that holds your repros.' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          command: { type: 'string', description: 'The exact command, runnable from the worktree root.' },
          output: { type: 'string', description: 'What the command printed.' },
          expected: { type: 'string', description: 'What the intent requires it to print.' },
        },
        required: ['title', 'command', 'output', 'expected'],
      },
    },
  },
  required: ['worktree', 'findings'],
}
const VERDICT = {
  type: 'object',
  properties: {
    reproduced: { type: 'boolean', description: 'The rerun showed the failure the finding describes.' },
    breaksIntent: { type: 'boolean', description: 'That failure contradicts the stated intent.' },
    output: { type: 'string', description: 'What the rerun printed.' },
    reason: { type: 'string' },
  },
  required: ['reproduced', 'breaksIntent', 'output', 'reason'],
}

const labelOf = (adversary, index) => adversary.label || `adversary-${index + 1}`
const breakPrompt = [
  `Scope: ${scope}`,
  `Intent: ${intent}`,
  patchPath ? `The scope includes uncommitted changes. Apply them first with \`git apply ${patchPath}\`.` : '',
  'Break this change. Prove each finding with a run against the real code, such as a failing test, a repro script, or command output that shows the wrong behavior. For a design or plan, run a prototype or probe the current tree. Keep repros in your own worktree. Report each finding with a title, the exact command, the output it printed, and the output the intent requires. Leave out anything you did not run. That covers style, naming, structure, and risks that need a future change to matter. No findings is a valid result.',
].filter(Boolean).join('\n\n')
const real = finding => Boolean(finding.verdict && finding.verdict.reproduced && finding.verdict.breaksIntent)

const perAdversary = await pipeline(
  adversaries,
  (adversary, _, index) => {
    const opts = { label: labelOf(adversary, index), phase: 'Break', schema: FINDINGS, agentType: 'general-purpose', isolation: 'worktree' }
    for (const key of ['model', 'effort']) if (adversary[key]) opts[key] = adversary[key]
    return agent(breakPrompt, opts)
  },
  async (report, adversary, index) => {
    const label = labelOf(adversary, index)
    const verdicts = await parallel(report.findings.map(finding => () => agent([
      `Rerun one reported failure and say whether it is real. Work in ${report.worktree}. Do not edit any file there.`,
      `Intent of the change: ${intent}`,
      `Finding: ${finding.title}`,
      `Command: ${finding.command}`,
      `Reported output: ${finding.output}`,
      `Output the intent requires: ${finding.expected}`,
      'Run the command exactly as written. Report what it printed. Default to reproduced=false when the run does not show the failure.',
    ].join('\n\n'), { label: `verify:${label}:${finding.title}`.slice(0, 60), phase: 'Verify', schema: VERDICT, agentType: 'general-purpose' })))
    const judged = report.findings.map((finding, i) => ({ ...finding, foundBy: label, worktree: report.worktree, verdict: verdicts[i] }))
    return {
      label,
      verified: judged.filter(real),
      dropped: judged.filter(f => !real(f)).map(f => ({ title: f.title, reason: f.verdict ? f.verdict.reason : 'the verifier returned nothing' })),
    }
  },
)

const gaps = adversaries.map(labelOf).filter((_, index) => !perAdversary[index])
if (gaps.length) log(`No result from ${gaps.join(', ')}.`)
const done = perAdversary.filter(Boolean)
return {
  findings: done.flatMap(a => a.verified),
  dropped: done.map(a => ({ label: a.label, count: a.dropped.length, findings: a.dropped })),
  gaps,
}
