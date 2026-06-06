# Assistant Response Strategy v0

Date: 2026-06-06

## Product Rule

The archive assistant has two response layers:

1. Instant Assistant
2. Research

Instant Assistant must feel immediate. Target latency is under 5 seconds after
the user sends a normal question. It must not block on Qwen, WebGPU, ONNX
files, or any generation model. It answers first from:

- active surface context;
- deterministic archive retrieval candidates;
- image-state policy;
- source and rights metadata;
- short response scripts.

After the scripted answer is visible, the UI may ask Qwen3.5-0.8B for a very
short fast-refine pass. That pass must be bounded by a small time budget. If it
returns quickly, it may replace the same answer with a slightly better phrasing;
if it misses the budget, it is ignored. The user should not wait for it.

Qwen3.5-0.8B is still called from ordinary Assistant when possible, but only as
a non-blocking fast-refine layer over the already visible scripted answer. The
ordinary answer must never wait for model load or generation.

Research is the only path that waits for Qwen3.5-0.8B. Research is for longer
interpretive synthesis, relation mapping, or multi-record reading support. It
may take longer and must remain visibly distinct from ordinary Assistant use.

Qwen may also be prewarmed in the background after Assistant opens. Prewarming
is not a visible loading step and must not disable ordinary scripted answers.

## Tone

The assistant should sound like a concise archive research aide, not a generic
chatbot. It should:

- start from the current archive record;
- name uncertainty without apologizing too much;
- avoid canon claims unless framed as current-archive navigation;
- cite surface IDs, source names, and image states when available;
- keep ordinary answers to one short paragraph;
- avoid hallucinated external facts;
- avoid saying copyright unless the user asks about copying, downloading,
  reproducing, or rights.

## Scripted Ordinary Answers

Current work:

> This page is best read as a source-linked object record: title, date, image
> state, and source are enough to orient the work. Use it as a starting point,
> then open the source before making a stronger historical claim.

Recommendation:

> In the current archive, start with the highest-ranked candidate. This is an
> archive-navigation pick based on date, region, image state, source visibility,
> and graphic-design signals, not an objective canon.

Rights/image:

> Treat the image state as display evidence, not a permission shortcut. IMG03
> can support open-image use; IMG01 and IMG02 stay source-linked unless a
> stricter rights review upgrades them.

Source:

> Use the source name and source URL as the first citation layer. The archive
> note can guide reading, but the source page remains the authority for object
> metadata and rights evidence.

Next check:

> Compare the retrieved archive candidates first. That keeps the reading
> grounded in source-visible records instead of drifting into general
> design-history claims.

## Implementation Binding

- `frontend/src/lib/assistant-instant.ts` owns ordinary Assistant response
  scripts and intent handling.
- `frontend/src/lib/assistant-retrieval.ts` owns deterministic candidate
  retrieval and structured evidence rows.
- `frontend/src/lib/qwen35-adapter.ts` is used by Research and by the ordinary
  fast-refine pass.
- Ordinary Assistant must not wait for `createQwenAssistantSession`; it may
  start or reuse the session only as a background refinement layer.
- `Qwen/Qwen3.5-0.8B` is the only model identity. No Llama, hosted API,
  WebLLM catalog fallback, or alternate local generation model is permitted.
