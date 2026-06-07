# Browser-Local Qwen RAG Independent Research Brief v0

Date: 2026-06-07

## Purpose

This document defines an independent research repo/lab direction for the
archive assistant bottleneck: browser-local Qwen3.5-0.8B over a large,
rights-aware private/public archive dataset. It is not a product-rule change,
not a mainline feature branch, and does not authorize a different assistant
model, hosted inference path, or evidence policy.

The research repo is independent from the archive product repository. Research
results may inform later product decisions, but experimental code, runtime
comparisons, benchmark outputs, and model artifacts should not be merged into
the product archive unless a separate product decision accepts them.

The research problem is not simply "make the model faster." It is an
end-to-end system problem:

- retrieve a small, high-value evidence packet from a large archive;
- preserve privacy, citation, and rights boundaries;
- use a browser-local small model for conversational guidance;
- reduce perceived and measured latency without turning Assistant into Search;
- maintain answer faithfulness under strict source-evidence constraints.

## Fixed Project Constraints

The current product constraints remain binding unless a later reviewed decision
changes them:

- Model identity: `Qwen/Qwen3.5-0.8B`.
- Browser runtime artifact: `onnx-community/Qwen3.5-0.8B-ONNX`.
- Current frontend path: Transformers.js / ONNX browser execution with the
  text-only `Qwen3_5ForCausalLM` class.
- No Llama, WebLLM catalog fallback, hosted API fallback, or alternate
  generation model in product Assistant.
- Deterministic Search remains available without model load.
- Assistant output is a reading aid, not archive evidence.
- AI output must not create, upgrade, or certify rights states.
- No image download for assistant research.
- Image context remains governed by project image-state rules: IMG03/open image
  material may be eligible for stricter future model-image experiments; IMG00,
  IMG01, IMG02, and IMG04 must not be silently promoted.

The independent research repo/lab may benchmark alternative runtimes such as
WebLLM/MLC or ONNX Runtime WebGPU only as experiments. Those experiments must be
documented as non-product comparisons until accepted by a project decision
record.

## Observed Baseline

Local project notes establish the practical baseline:

- long, raw archive context makes Qwen slow and less reliable;
- no-evidence questions must be blocked before model invocation;
- deterministic retrieval/search is fast enough and should produce the facts;
- Qwen should synthesize, advise, caveat, and suggest next reading moves;
- regular Assistant should target a short answer, while Research may use a
  broader evidence packet;
- previous Node/CPU probes showed compact micro-note generation still taking
  seconds, so browser WebGPU, prompt size, token budget, and cache behavior must
  be measured separately.

## Bottleneck Taxonomy

Measure the whole path instead of only model token generation.

| Layer | Possible bottleneck | Required measurement |
|---|---|---|
| Model discovery | Wrong artifact, cold network fetch, browser cache miss | artifact URL, bytes fetched, cache hit/miss, load time |
| Runtime init | WebGPU adapter/device setup, CPU/WASM fallback, worker startup | device type, execution provider, init time, fallback reason |
| Memory | model weights, KV cache, prompt tensors, stale sessions | memory estimate, WebGPU errors, recovery path |
| Retrieval | broad candidate set, slow client filtering, weak ranking | retrieval time, candidate count, hit@k, MRR |
| Evidence compression | oversized notes, repeated source metadata, noisy context | prompt bytes, prompt tokens, field retention |
| Prompt planning | weak intent routing, overlong system text, bad answer contract | intent class, answer lane, max tokens, failure cases |
| Tokenization | large chat template, repeated history, no cache reuse | tokenization time, input tokens |
| Generation | overlarge `max_new_tokens`, thinking mode, sampling overhead | TTFT, total latency, token/s, output tokens |
| UI integration | main-thread blocking, non-streamed output, panel re-render | thread blocking, perceived latency, spinner duration |
| Conversation memory | stale context, overlong retained turns, wrong page carryover | memory size, age, page-distance clearing |

## Research Questions

1. What proportion of response time comes from retrieval, prompt construction,
   tokenization, runtime initialization, first token, and generation?
2. Can deterministic intent routing and evidence compression make Qwen useful
   within a short-answer budget without replacing Qwen with a template?
3. Which retrieval shape works best for a 0.8B model: keyword, field/facet,
   hybrid keyword plus embedding, graph/topology-aware retrieval, or lightweight
   reranking?
4. How small can the evidence packet become before answer quality drops?
5. How should same-page memory, browser model cache, and WebGPU session cache be
   managed to avoid crashes and stale answers?
6. Can Research mode use a broader packet without causing WebGPU buffer errors?
7. Which failures are model capability limits and which are product-pipeline
   bugs?
8. What benchmark can this archive contribute to browser-local, rights-aware
   small-model RAG research?

## Candidate System Architecture

The likely architecture is a layered RAG system rather than a single prompt.

1. Query classifier
   - Detect route: archive orientation, current object, first/earliest query,
     comparison, rights/source question, recommendation, method question,
     no-evidence/general chat.
   - Select answer lane: instant, assistant, research, refusal, or search-only.

2. Deterministic retrieval
   - Use existing archive payload fields first: title, date, region, source,
     image state, rights note, surface type, page type, folder route.
   - Use time/region filters for queries such as "1970s France" before
     semantic expansion.
   - Return stable IDs and source URLs before any generated prose.

3. Topology-aware expansion
   - Add relation-aware context from the current main sheet, nearby main
     sheets, sub sheets, text pages, appendix cards, and source family.
   - Treat this as graph/navigation evidence, not historical proof.

4. Optional local semantic layer
   - Add browser-local embeddings or a build-time index for text chunks.
   - Use semantic retrieval only to improve candidate recall; keep source
     fields visible and citeable.

5. Evidence compressor
   - Convert candidates into a compact evidence packet:
     `id`, `title`, `date`, `region`, `source`, `rights`, `why matched`,
     `limits`, and one short source note.
   - Remove raw JSON, duplicate prose, long appendix text, and unrelated
     page-sequence text.

6. Qwen synthesis
   - Assistant mode: one short, complete, useful answer with a caveat or next
     move when needed.
   - Research mode: longer but still evidence-bound synthesis, relation map,
     and next checks.
   - No historical claim beyond retrieved evidence.

7. Runtime manager
   - Keep model load, generation, and recovery off the main UI thread when
     possible.
   - Measure and expose internal timing during development only.
   - Clear failed WebGPU sessions after buffer/device errors.

## Experiment Matrix

| Experiment | Control | Variant | Measure |
|---|---|---|---|
| Runtime backend | current Transformers.js WebGPU path | ONNX Runtime WebGPU direct path, WebLLM/MLC comparison | load, TTFT, token/s, crash rate |
| Model class | text-only CausalLM | vision-language artifact only as non-product experiment | memory, latency, image-policy feasibility |
| Retrieval breadth | top 1 compact lead | top 3, top 8, topology-expanded | quality, latency, hallucination rate |
| Prompt size | current fast packet | 50%, 25%, field-only packet | answer usefulness and completion |
| Answer lane | Assistant | Research | latency, output quality, refusal correctness |
| Memory policy | no memory | 3-minute same-page memory, page-distance clearing | continuity, stale-answer rate |
| Cache policy | remote artifact cache | packaged public model path, immutable headers, service worker cache | cold load, warm load, failures |
| Search integration | keyword-only | hybrid lexical plus embedding plus graph hints | hit@k, MRR, user-picked result |

## Metrics

Performance metrics:

- cold model load time;
- warm model load time;
- retrieval time;
- prompt construction time;
- tokenization time;
- time to first token / first visible answer;
- total response time;
- output tokens and tokens per second;
- prompt tokens and context bytes;
- browser memory estimate where available;
- WebGPU device error rate and recovery success.

Quality metrics:

- citation faithfulness;
- answer completeness under the requested answer lane;
- refusal correctness for no-evidence questions;
- no invention of title, creator, date, citation, source, or rights state;
- usefulness rating on archive-navigation tasks;
- whether the answer does more than repeat Search results;
- whether it gives a credible next reading move.

Archive-specific metrics:

- source-visible preservation;
- verified-open preservation;
- IMG state compliance;
- region/time coverage relevance;
- no AI-derived source upgrade;
- no raw image copying.

## Candidate Paper Contributions

Possible contributions if the research produces strong evidence:

- A rights-aware browser-local RAG benchmark for visual archive systems.
- Evidence-packet compression for 0.8B local generators over large archives.
- A UI-aware answer-lane design: Search, Assistant, Research, and refusal as
  distinct latency/quality contracts.
- A WebGPU runtime failure taxonomy for browser-local archive assistants.
- A topology-aware retrieval method that uses dossier structure without turning
  folder membership into historical proof.

This is likely a systems-plus-HCI-plus-digital-archives contribution rather
than a pure model-compression paper unless the runtime experiments produce a
new reusable WebGPU optimization.

## Literature And System Starting Points

Primary implementation references to verify and cite in the independent
research repo/lab:

- WebLLM / MLC in-browser inference and worker support:
  https://github.com/mlc-ai/web-llm
- WebLLM paper:
  https://arxiv.org/abs/2412.15803
- Transformers.js WebGPU guide:
  https://huggingface.co/docs/transformers.js/en/guides/webgpu
- ONNX Runtime WebGPU execution provider:
  https://onnxruntime.ai/docs/tutorials/web/ep-webgpu.html
- Qwen3.5-0.8B model card:
  https://huggingface.co/Qwen/Qwen3.5-0.8B
- ONNX runtime artifact:
  https://huggingface.co/onnx-community/Qwen3.5-0.8B-ONNX
- Chrome model caching guidance:
  https://developer.chrome.com/docs/ai/cache-models
- MiniRAG:
  https://arxiv.org/abs/2501.06713
- DRAGON distributed RAG / speculative aggregation:
  https://arxiv.org/abs/2504.11197
- Speculative RAG:
  https://arxiv.org/abs/2407.08223
- KIVI KV-cache quantization:
  https://arxiv.org/abs/2402.02750
- TurboQuant:
  https://huggingface.co/papers/2504.19874

Research notes must distinguish primary sources, papers, community reports, and
unverified blog/news claims. Browser/WebGPU performance claims must be tested on
the actual target hardware before they become project conclusions.

## Non-Goals

- Do not replace deterministic Search with generated text.
- Do not send private archive data or restricted image content to a hosted
  model for normal product operation.
- Do not train or fine-tune on copyrighted/private data without a separate
  rights and ethics review.
- Do not use AI answers as source evidence, rights evidence, or classification
  authority.
- Do not optimize by hiding uncertainty or removing citation constraints.
- Do not reintroduce Llama or generic WebLLM model selection into product
  Assistant.

## Deliverables For The Next Research Window

1. A source-verified annotated bibliography.
2. A measured latency decomposition for the current frontend.
3. A browser benchmark harness that records retrieval, prompt, tokenization,
   TTFT, total latency, token/s, memory errors, and cache state.
4. A query set covering archive orientation, object reading, first/earliest
   claims, region-period recommendations, rights questions, and no-evidence
   refusals.
5. A retrieval and prompt-compression ablation report.
6. A proposed implementation plan with product-safe stages.
7. A paper framing memo with title options, abstract, contributions, related
   work, limitations, and venue fit.
