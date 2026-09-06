import { createHash, randomUUID } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, readdirSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { execFileSync } from 'node:child_process';

export const SURFACES = ['SEARCH_RESULTS', 'TRACE_CONTEXT', 'TRACE_VALIDATED_EXPLORATION', 'TRACE_OPEN_INQUIRY'];
export const MAX_CAMPAIGN_ATTEMPTS = 130;
export function buildPlan(cases, configurations, repetitions = 3) {
  const plan = [];
  for (const configuration of configurations) {
    const entries = cases.flatMap(item => Array.from({ length: repetitions }, (_, index) => ({
      ...item, configuration, repetition: index + 1,
      entry_id: `${configuration.id}:${item.id}:${index + 1}`,
    })));
    const initial = SURFACES.map(surface => entries.find(item => item.surface === surface && item.repetition === 1));
    if (initial.some(item => !item)) throw new Error('Four active surfaces required');
    const selected = new Set(initial.map(item => item.entry_id));
    plan.push(...initial.map(item => ({ ...item, stage: 'INITIAL_SURFACE_CHECK' })),
      ...entries.filter(item => !selected.has(item.entry_id)).map(item => ({ ...item, stage: 'REMAINING_CASES' })));
  }
  if (new Set(plan.map(item => item.entry_id)).size !== plan.length) throw new Error('Duplicate plan identity');
  return plan;
}
function metrics(plan, rows) {
  const executed = rows.filter(row => row.execution === 'EXECUTED');
  const attempted = executed.filter(row => row.provider_requests_sent > 0);
  const actual = attempted.reduce((sum, row) => sum + row.provider_requests_sent, 0);
  const effective = attempted.filter(row => row.source_class === 'MODEL' && row.schema_passed && row.gate_passed && !row.cache_hit).length;
  const identities = new Set(executed.map(row => row.entry_id));
  const complete = plan.length > 0 && identities.size === plan.length && plan.every(entry => identities.has(entry.entry_id)) && executed.length === plan.length && actual === plan.length && executed.every(row => row.provider_requests_sent === 1 && !row.cache_hit);
  const latencies = attempted.map(row => row.latency_ms).filter(Number.isFinite).sort((a,b) => a-b);
  const percentile = p => latencies.length ? latencies[Math.ceil(p * latencies.length) - 1] : null;
  const reasons = {};
  for (const row of executed) if (row.source_class === 'STATIC_FALLBACK') reasons[row.provider_status] = (reasons[row.provider_status] ?? 0) + 1;
  return { planned: plan.length, executed: executed.length, not_executed: plan.length-executed.length,
    actual_requests: actual, effective_outputs: effective, effective_rate: actual ? effective/actual : null,
    schema_passed: attempted.filter(row => row.schema_passed).length, gate_passed: attempted.filter(row => row.gate_passed).length,
    model_used: attempted.filter(row => row.source_class === 'MODEL').length,
    cache_hits: executed.filter(row => row.cache_hit).length, static_fallback: Object.values(reasons).reduce((a,b) => a+b,0),
    fallback_reasons: reasons, p50_ms: percentile(.5), p95_ms: percentile(.95),
    usage: attempted.reduce((sum,row) => { for (const key of ['input_tokens','output_tokens','total_tokens']) if (Number.isFinite(row.usage?.[key])) sum[key]=(sum[key]??0)+row.usage[key];return sum; },{}),
    complete, target_met: complete && effective >= Math.ceil(plan.length * .95) };
}
export function summarize(plan, rows, stopReason = null) {
  const configurations = [...new Set(plan.map(item => item.configuration.id))].map(id => {
    const groupPlan = plan.filter(item => item.configuration.id === id);
    const groupRows = rows.filter(row => row.configuration.id === id);
    return { configuration: groupPlan[0].configuration, ...metrics(groupPlan, groupRows),
      surfaces: Object.fromEntries(SURFACES.map(surface => [surface, metrics(groupPlan.filter(item => item.surface === surface), groupRows.filter(row => row.surface === surface))])) };
  });
  const all = metrics(plan, rows);
  const blocked = ['NO_KEY','REDIS_MISSING','REDIS_UNAVAILABLE','PROVIDER_DISABLED','INVALID_CONFIGURATION','AUTHENTICATION','BILLING','PROVIDER_CONFIGURATION'].includes(stopReason);
  const status = blocked ? 'BLOCKED_ENVIRONMENT' : !all.complete || stopReason ? 'INCOMPLETE' : configurations.every(group => group.target_met) ? 'PASS' : 'FAIL';
  return { status, exit_code: status === 'PASS' ? 0 : blocked ? 2 : 1, stop_reason: stopReason,
    ...all, configurations, content_review: 'REQUIRES_INDEPENDENT_REVIEW' };
}
export async function runPlan({ plan, prerequisites, attempt, record = () => {}, completedRows = [] }) {
  const completed = new Map(completedRows.map(row=>[row.entry_id,row]));
  if(completed.size!==completedRows.length || completedRows.some(row=>row.execution!=='EXECUTED'||!plan.some(entry=>entry.entry_id===row.entry_id)))throw new Error('Invalid continuation rows');
  const rows = [];
  let stopReason = prerequisites.keyPresent ? prerequisites.redisConfigured ? prerequisites.modeAllowed ? null : 'PROVIDER_DISABLED' : 'REDIS_MISSING' : 'NO_KEY';
  if (!stopReason && prerequisites.invalidConfiguration) stopReason = 'INVALID_CONFIGURATION';
  if (!stopReason && prerequisites.redisReady === false) stopReason = 'REDIS_UNAVAILABLE';
  const initial = new Map();
  for (const entry of plan) {
    if(completed.has(entry.entry_id)){const row={...completed.get(entry.entry_id),inherited:true};rows.push(row);record(row);continue;}
    if (!stopReason && entry.stage === 'REMAINING_CASES' && initial.get(entry.configuration.id) === false) stopReason = 'INITIAL_SURFACE_CHECK_FAILED';
    if (stopReason) {
      const row = { ...entry, execution:'NOT_EXECUTED', provider_requests_sent:0, reason:stopReason };
      rows.push(row); record(row); continue;
    }
    let result;
    try { result = await attempt(entry); }
    catch (error) {
      stopReason = ['BUDGET_EXHAUSTED','SOURCE_CHANGED','REDIS_UNAVAILABLE','RATE_LIMIT_REACHED'].includes(error.code) ? error.code : 'RUNNER_ERROR';
      const row = { ...entry, execution:'NOT_EXECUTED', provider_requests_sent:0, reason:stopReason };
      rows.push(row); record(row); continue;
    }
    const row = { ...entry, ...result, execution:'EXECUTED' };
    rows.push(row); record(row);
    if (entry.stage === 'INITIAL_SURFACE_CHECK') {
      const valid = row.provider_requests_sent === 1 && row.schema_passed && row.gate_passed && row.source_class === 'MODEL' && !row.cache_hit;
      initial.set(entry.configuration.id, (initial.get(entry.configuration.id) ?? true) && valid);
    }
    if (row.fatal_category) stopReason = row.fatal_category;
    else if (row.provider_status === 'LIMITER_UNAVAILABLE') stopReason = 'REDIS_UNAVAILABLE';
  }
  return { rows, summary: summarize(plan, rows, stopReason) };
}
export function fatalCategory(httpStatus) {
  if ([401,403].includes(httpStatus)) return 'AUTHENTICATION';
  if (httpStatus === 402) return 'BILLING';
  if ([400,404,405,415,422].includes(httpStatus)) return 'PROVIDER_CONFIGURATION';
  return null;
}
export function createRunDirectory(root) {
  mkdirSync(root, {recursive:true});
  const id = `${new Date().toISOString().replace(/[:.]/g,'-')}-${randomUUID().slice(0,8)}`;
  const directory = join(root,id); mkdirSync(directory);
  return {id,directory};
}
// A single durable ledger covers live runs AND instrumented production HTTP/browser attempts.
// Reserve before fetch. A crash consumes a slot conservatively. Never reset this campaign implicitly.
export function reserveAttempt(file, metadata, cap = MAX_CAMPAIGN_ATTEMPTS) {
  if (!Number.isInteger(cap) || cap < 1 || cap > MAX_CAMPAIGN_ATTEMPTS) throw new Error('Invalid campaign cap');
  mkdirSync(join(file,'..'),{recursive:true});
  const lock = `${file}.lock`;
  try { mkdirSync(lock); } catch { throw Object.assign(new Error('Budget lock unavailable'),{code:'BUDGET_EXHAUSTED'}); }
  try {
    let ledger;
    try { ledger = existsSync(file) ? JSON.parse(readFileSync(file,'utf8')) : {limit:cap,attempts:[]}; }
    catch { throw Object.assign(new Error('Invalid campaign ledger'),{code:'BUDGET_EXHAUSTED'}); }
    if (!ledger || !Number.isInteger(ledger.limit) || ledger.limit < 1 || ledger.limit > MAX_CAMPAIGN_ATTEMPTS || !Array.isArray(ledger.attempts) || ledger.attempts.length >= Math.min(cap,ledger.limit)) throw Object.assign(new Error('Campaign budget exhausted'),{code:'BUDGET_EXHAUSTED'});
    ledger.attempts.push({ ...metadata, number:ledger.attempts.length+1, at:new Date().toISOString() });
    const temp = `${file}.${process.pid}.tmp`;writeFileSync(temp,JSON.stringify(ledger,null,2)+'\n');renameSync(temp,file);
    return ledger.attempts.length;
  } finally { rmSync(lock,{recursive:true}); }
}
export function sourceSnapshot(frontendRoot) {
  const files = {};
  const include = ['src/features/system-suggestions','src/app/api/system-suggestions','src/app/search',
    'src/features/search-v2/ui','src/app/@modal/(.)search','src/app/trace/exploration/desktop','src/app/trace/context-canvas/desktop',
    'src/features/trace-v49/exploration-ui','src/features/trace-v49/context/canvas',
    'next.config.ts','package.json','package-lock.json'];
  function visit(path) {
    if (!existsSync(path)) return;
    if (statSync(path).isDirectory()) { for (const entry of readdirSync(path)) visit(join(path,entry)); }
    else files[relative(frontendRoot,path)] = createHash('sha256').update(readFileSync(path)).digest('hex');
  }
  for (const name of include) visit(join(frontendRoot,name));
  for (const name of readdirSync(join(frontendRoot,'scripts')).filter(name => /system-suggestions-(?:live|runner)|system-suggests-live/.test(name))) visit(join(frontendRoot,'scripts',name));
  const sorted=Object.fromEntries(Object.entries(files).sort(([a],[b])=>a.localeCompare(b)));
  return {head:execFileSync('git',['rev-parse','HEAD'],{cwd:frontendRoot,encoding:'utf8'}).trim(),fingerprint:createHash('sha256').update(JSON.stringify(sorted)).digest('hex'),files:sorted};
}
