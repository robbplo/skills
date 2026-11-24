export const meta = {
  name: 'arena-run',
  description: 'Run every arena candidate on the same task in its own checkout, then have one judge score them against the rubric',
  whenToUse: 'Phases B and C of the pstack arena skill',
  phases: [
    { title: 'Candidates', detail: 'one agent per runner, same task' },
    { title: 'Cross-judge', detail: 'one judge scores every candidate' },
  ],
}

const input = typeof args === 'string' ? JSON.parse(args) : args
const { task, grounding, candidates, rubric, judge } = input || {}
if (typeof task !== 'string' || !Array.isArray(candidates) || candidates.length === 0 || !Array.isArray(rubric) || rubric.length === 0) {
  throw new Error('arena-run needs args {task, rubric: [criterion], candidates: [{label?, model?, effort?, outputPath?}], grounding?, judge?: {model?, effort?}}')
}

const CANDIDATE = {
  type: 'object',
  properties: {
    location: { type: 'string', description: 'Absolute path of the artifact, plus the branch and commit when it is in a git checkout.' },
    summary: { type: 'string', description: 'What you built, in a few sentences.' },
    rationale: { type: 'string', description: 'The alternatives you considered and what you rejected.' },
  },
  required: ['location', 'summary', 'rationale'],
}
const VERDICT = {
  type: 'object',
  properties: {
    scores: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          label: { type: 'string' },
          criteria: {
            type: 'array',
            items: {
              type: 'object',
              properties: { criterion: { type: 'string' }, score: { type: 'integer', minimum: 1, maximum: 5 }, note: { type: 'string' } },
              required: ['criterion', 'score', 'note'],
            },
          },
        },
        required: ['label', 'criteria'],
      },
    },
    base: { type: 'string', description: 'The label of the candidate to build on.' },
    rationale: { type: 'string' },
  },
  required: ['scores', 'base', 'rationale'],
}

const labelOf = (candidate, index) => candidate.label || `candidate-${index + 1}`
const candidatePrompt = candidate => [
  task,
  grounding ? `Shared grounding: ${grounding}` : '',
  candidate.outputPath
    ? `Write the artifact under ${candidate.outputPath} and nowhere else.`
    : 'You are in your own git worktree. Build the artifact there and commit it.',
  'Report where the artifact is, what you built, and the alternatives you considered and rejected.',
].filter(Boolean).join('\n\n')

phase('Candidates')
const built = await parallel(candidates.map((candidate, index) => () => {
  const opts = { label: labelOf(candidate, index), phase: 'Candidates', schema: CANDIDATE, agentType: 'general-purpose' }
  for (const key of ['model', 'effort']) if (candidate[key]) opts[key] = candidate[key]
  if (!candidate.outputPath) opts.isolation = 'worktree'
  return agent(candidatePrompt(candidate), opts)
}))

const finished = candidates.map((candidate, index) => built[index] && { label: labelOf(candidate, index), ...built[index] }).filter(Boolean)
const dropouts = candidates.map(labelOf).filter(label => !finished.some(c => c.label === label))
if (dropouts.length) log(`No artifact from ${dropouts.join(', ')}. Proceeding with ${finished.length}.`)

let verdict = null
if (judge && finished.length > 1) {
  phase('Cross-judge')
  const opts = { label: 'cross-judge', phase: 'Cross-judge', schema: VERDICT, agentType: 'Explore' }
  for (const key of ['model', 'effort']) if (judge[key]) opts[key] = judge[key]
  verdict = await agent([
    'Judge these candidates for one task. Read each artifact end to end. Do not edit any file.',
    `Task: ${task}`,
    `Rubric:\n${rubric.map((criterion, i) => `${i + 1}. ${criterion}`).join('\n')}`,
    `Candidates:\n${finished.map(c => `- ${c.label}: ${c.location}`).join('\n')}`,
    'Score every candidate on every criterion from 1 to 5 with a one-line note. Then recommend one base and say why.',
  ].join('\n\n'), opts).catch(() => null)
  if (!verdict) log('The cross-judge returned nothing. Pick the base alone.')
}

return { candidates: finished, dropouts, verdict }
