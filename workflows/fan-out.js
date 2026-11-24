export const meta = {
  name: 'fan-out',
  description: 'Run every brief as its own agent in parallel, retry a dropout once, and return one report per brief',
  whenToUse: 'The fan-out phase of the pstack swarm, arena, and interrogate skills',
  phases: [{ title: 'Fan out', detail: 'one agent per brief' }],
}

const input = typeof args === 'string' ? JSON.parse(args) : args
const briefs = input && input.briefs
if (!Array.isArray(briefs) || briefs.length === 0 || briefs.some(b => !b || typeof b.prompt !== 'string')) {
  throw new Error('fan-out needs args {briefs: [{prompt, label?, model?, effort?, isolation?, agentType?}]}')
}

const labelOf = (brief, index) => brief.label || `worker-${index + 1}`
const run = (brief, index) => {
  const opts = { label: labelOf(brief, index), phase: 'Fan out', agentType: brief.agentType || 'general-purpose' }
  for (const key of ['model', 'effort', 'isolation']) if (brief[key]) opts[key] = brief[key]
  return agent(brief.prompt, opts)
}

phase('Fan out')
const reports = await parallel(briefs.map((brief, index) => async () => {
  const first = await run(brief, index).catch(() => null)
  if (first) return first
  log(`${labelOf(brief, index)} returned nothing. Retrying once.`)
  return run(brief, index)
}))

const results = briefs.map((brief, index) => ({ label: labelOf(brief, index), report: reports[index] || null }))
const gaps = results.filter(r => r.report === null).map(r => r.label)
if (gaps.length) log(`No report from ${gaps.join(', ')}. Each is a gap, not a pass.`)
return { results, gaps }
