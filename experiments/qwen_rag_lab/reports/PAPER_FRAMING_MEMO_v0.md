# Paper Framing Memo v0

## Working Titles

1. Browser-Local Small-Model RAG for Rights-Aware Design Archives
2. Evidence-Packet Compression for Browser-Local Archive Assistants
3. Rights-Aware Retrieval and UI-Aware Generation in a Browser Archive Assistant
4. Making a 0.8B Browser Model Useful for Archive Navigation
5. WebGPU Failure, Evidence Compression, and Faithfulness in Browser-Local Archive RAG

## Abstract Draft

We study how a browser-local small language model can support reading and
navigation over a rights-aware archive of modern graphic design without becoming
an evidentiary authority. The system fixes the generation model as
`Qwen/Qwen3.5-0.8B` and treats runtime alternatives as research-only
comparisons, forcing optimization to happen at the RAG and interface layers
rather than through model substitution. We propose deterministic retrieval,
bounded topology expansion, compact evidence packets, and UI-aware answer lanes
for Assistant, Research, and refusal behavior. The benchmark records retrieval
time, prompt size, cold/warm model state, tokenization, TTFT, total latency,
tokens per second, WebGPU failures, source/rights preservation, and
faithfulness. The broader contribution is a reproducible method for making
local small-model RAG useful under archive privacy, citation, and rights
constraints.

## Core Contributions

- A rights-aware archive RAG benchmark that separates evidence retrieval from
  generated prose.
- A typed evidence-packet design for 0.8B browser-local generation.
- A query-lane taxonomy linking retrieval breadth, evidence fields, output
  length, refusal behavior, and latency expectations.
- A runtime measurement schema for cold/warm load, TTFT, tokens/s, and WebGPU
  failure recovery.
- A paper-safe distinction between product runtime constraints and
  research-only runtime comparisons.

## Related Work Clusters

- Browser-local inference: Transformers.js, ONNX Runtime WebGPU, WebLLM/MLC,
  workers, service workers, and browser model caching.
- Small-model RAG: compact retrieval, graph/topology-aware retrieval, hybrid
  lexical/semantic retrieval, and lightweight reranking.
- Prompt and context compression: evidence density, lost-in-the-middle effects,
  and answer-lane budgeting.
- RAG evaluation: faithfulness, refusal correctness, retrieval hit@k/MRR,
  usefulness, and latency.
- Rights-aware cultural heritage: standardized rights metadata, source
  authority, reuse caveats, and image-state compliance.

## Benchmark Description

The benchmark uses safe archive fixture records containing surface ids, titles,
dates, regions, source links, rights labels, image-state, topology hints, and
compact source-derived notes. It excludes raw HTML, model files, images,
cookies, sessions, browser cache, and AI-generated evidence.

The query set covers archive orientation, current-object explanation,
first/earliest claims, region-period recommendations, source/rights questions,
comparison, no-evidence refusal, method/process questions, more-context
requests, and casual archive help.

## Experiment Plan

1. Retrieval-only baseline and evidence-packet ablation.
2. Qwen fast answer with top-3 compressed source/rights packets.
3. Qwen Research answer with top-8 packets and topology hints.
4. Cold/warm model load and browser cache measurement.
5. Worker vs main-thread measurement.
6. Research-only comparison among Transformers.js, ONNX Runtime WebGPU, and
   WebLLM/MLC, with no product-path implication.
7. Manual answer-quality scoring for faithfulness, rights/source preservation,
   usefulness, and refusal correctness.

## Limitations

- Hardware, browser version, cache state, and WebGPU adapter behavior will
  strongly affect runtime results.
- Native model context length must not be treated as browser-effective context
  length until measured.
- Server-side KV-cache and speculative decoding literature may not transfer to
  browser WebGPU.
- Fixture-level benchmark results do not establish full archive-scale recall.

## Ethics And Rights

The assistant is a reader over source evidence, not a rights adjudicator. Rights
labels must remain retrieved metadata. Source archives remain authoritative.
Generated prose must never upgrade rights status, create evidence, or convert a
reading suggestion into a historical claim.

## Venue Fit

JCDL is the strongest fit if the archive/evidence benchmark is central. CHI is
plausible if UI-aware latency, trust, and answer-lane interaction become the
main contribution. SIGIR is plausible if the retrieval/evaluation method and
evidence-packet compression results become the strongest part of the work.
