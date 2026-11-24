export const meta = {
  name: 'swarm-run',
  description: 'Run every swarm brief as its own worker, respawn a worker whose report is missing or incomplete once, and return one result per brief',
  whenToUse: 'Phase B of the pstack swarm skill',
  phases: [{ title: 'Fan out', detail: 'one worker per brief' }],
}

const input = typeof args === 'string' ? JSON.parse(args) : args
const briefs = input && input.briefs
if (!Array.isArray(briefs) || briefs.length === 0 || briefs.some(b => !b || typeof b.prompt !== 'string')) {
  throw new Error('swarm-run needs args {briefs: [{prompt, label?, model?, effort?, isolation?, mustRecord?}]}')
}

const REPORT = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['PASS', 'ISSUES', 'BLOCKED'] },
    evidence: { type: 'string', description: 'What you ran and what it printed, with every SHA and the method your brief names.' },
    issues: { type: 'array', items: { type: 'string' }, description: 'Every issue you can prove, one line each. Empty on PASS.' },
  },
  required: ['status', 'evidence', 'issues'],
}

const labelOf = (brief, index) => brief.label || `worker-${index + 1}`
const missing = (brief, report) => {
  if (!report) return 'no report'
  const text = `${report.evidence}\n${report.issues.join('\n')}`
  const absent = (brief.mustRecord || []).filter(token => !text.includes(token))
  return absent.length ? `did not record ${absent.join(', ')}` : null
}
const run = (brief, index) => {
  const opts = { label: labelOf(brief, index), phase: 'Fan out', schema: REPORT, agentType: 'general-purpose' }
  for (const key of ['model', 'effort', 'isolation']) if (brief[key]) opts[key] = brief[key]
  return agent(brief.prompt, opts).catch(() => null)
}

phase('Fan out')
const outcomes = await parallel(briefs.map((brief, index) => async () => {
  const label = labelOf(brief, index)
  let report = await run(brief, index)
  let reason = missing(brief, report)
  if (reason) {
    log(`${label}: ${reason}. Respawning once.`)
    report = await run(brief, index)
    reason = missing(brief, report)
  }
  return reason ? { label, gap: reason } : { label, ...report }
}))

const settled = briefs.map((brief, index) => outcomes[index] || { label: labelOf(brief, index), gap: 'no report' })
const results = settled.filter(o => !o.gap)
const gaps = settled.filter(o => o.gap).map(o => ({ label: o.label, reason: o.gap }))
if (gaps.length) log(`Gaps: ${gaps.map(g => g.label).join(', ')}. A gap is not a pass.`)
return { results, gaps }
