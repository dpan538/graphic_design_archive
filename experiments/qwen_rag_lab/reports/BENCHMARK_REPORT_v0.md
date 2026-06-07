# Benchmark Report v0

Generated: 2026-06-07T01:34:56.639Z

## Scope

This is the first research-lab baseline for browser-local Qwen RAG. It measures deterministic retrieval, evidence-packet construction, and packet-size ablations over a safe fixture. Qwen generation was not executed in this run, no model weights were downloaded, and no browser cache was written.

## Dataset

- Fixture records: 53
- Benchmark queries: 30
- Query categories: archive_orientation, casual_archive_help, current_object_explanation, source_rights_question, first_earliest_claim, comparison, region_period_recommendation, method_process_question, more_context, no_evidence_refusal
- Source fields retained: surface id, title, date, region, source name/url, rights label, image-state, topology hints, compact text notes.

## Initial Results

| Variant | Runs | Avg prompt bytes | Avg prompt tokens est. | Avg retrieval ms | Source/rights preserved | Refusal correct |
|---|---:|---:|---:|---:|---:|---:|
| top1_compressed_topology_source_rights | 30 | 1462 | 365 | 0.688 | 1 | 1 |
| top3_compressed_topology_source_rights | 30 | 3836 | 958 | 0.64 | 1 | 1 |
| top8_compressed_topology_source_rights | 30 | 5486 | 1369 | 0.588 | 1 | 1 |
| top3_raw_topology_source_rights | 30 | 4486 | 1119 | 0.62 | 1 | 1 |
| top3_compressed_no_topology_source_rights | 30 | 3221 | 804 | 0.596 | 1 | 1 |
| top3_compressed_topology_no_source_rights | 30 | 2839 | 708 | 0.606 | 0.1 | 1 |

## Readable Findings

- Top-1 compressed packets are the smallest baseline and preserve the strongest latency/prompt-size budget, but they are likely too brittle for comparison, chronology, and region-period routes.
- Top-3 compressed packets are the best first Assistant baseline because they keep source/rights fields visible while leaving room for a short Qwen answer.
- Top-8 packets should be reserved for Research mode and only after browser tokenization/TTFT are measured.
- Removing source/rights fields reduces prompt size but breaks the rights-aware archive contract, so this variant is a negative control rather than a product candidate.
- No-evidence queries are correctly blocked before generation in this benchmark harness.

## What Is Not Measured Yet

- Cold or warm Qwen model load.
- Browser tokenization time.
- TTFT and total generation latency.
- Tokens per second.
- WebGPU memory/device failure.
- Human faithfulness scores for generated answers.

## Next Measurement

Run the browser lab on target hardware with Qwen enabled only after the user intentionally supplies or enables the runtime path. Record cold/warm model load, prompt tokens, TTFT, total latency, output tokens, tokens/s, and WebGPU failures for the same query set.
