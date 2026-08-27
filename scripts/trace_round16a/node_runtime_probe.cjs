"use strict";

const fs = require("node:fs");
const { monitorEventLoopDelay } = require("node:perf_hooks");

const output = process.env.TRACE_RUNTIME_PROBE_PATH;
if (output) {
  const sessionId = process.env.TRACE_RUNTIME_PROBE_SESSION_ID || "UNSCOPED";
  const processRole = process.env.TRACE_RUNTIME_PROBE_ROLE || "NEXT_PRODUCTION_SERVER";
  const processStarted = process.hrtime.bigint();
  const histogram = monitorEventLoopDelay({ resolution: 10 });
  histogram.enable();
  let priorCpu = process.cpuUsage();
  let priorTime = process.hrtime.bigint();
  let sequence = 0;
  const write = (phase) => {
    const now = process.hrtime.bigint();
    const cpu = process.cpuUsage();
    const elapsedMicros = Number(now - priorTime) / 1_000;
    const cpuMicros = (cpu.user - priorCpu.user) + (cpu.system - priorCpu.system);
    const memory = process.memoryUsage();
    sequence += 1;
    const row = {
      timestamp_utc: new Date().toISOString(),
      probe_session_id: sessionId,
      probe_sequence: sequence,
      process_role: processRole,
      phase,
      pid: process.pid,
      ppid: process.ppid,
      process_uptime_ms: Number(now - processStarted) / 1_000_000,
      cpu_percent_interval: elapsedMicros > 0 ? (cpuMicros / elapsedMicros) * 100 : 0,
      cpu_user_micros_total: cpu.user,
      cpu_system_micros_total: cpu.system,
      rss_bytes: memory.rss,
      heap_used_bytes: memory.heapUsed,
      heap_total_bytes: memory.heapTotal,
      external_bytes: memory.external,
      event_loop_delay_mean_ms: Number.isFinite(histogram.mean) ? histogram.mean / 1e6 : 0,
      event_loop_delay_p95_ms: histogram.count > 0 ? histogram.percentile(95) / 1e6 : 0,
      event_loop_delay_p99_ms: histogram.count > 0 ? histogram.percentile(99) / 1e6 : 0,
      event_loop_delay_max_ms: histogram.max / 1e6,
    };
    fs.appendFileSync(output, `${JSON.stringify(row)}\n`, { encoding: "utf8", mode: 0o644 });
    priorCpu = cpu;
    priorTime = now;
    histogram.reset();
  };
  write("START");
  const timer = setInterval(() => write("SAMPLE"), 1_000);
  timer.unref();
  process.once("exit", () => {
    try { write("EXIT"); } catch { /* best-effort process-exit sample */ }
  });
}
