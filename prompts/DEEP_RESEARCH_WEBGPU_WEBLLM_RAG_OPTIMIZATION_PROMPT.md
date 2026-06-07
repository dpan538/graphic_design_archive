# Deep Research Prompt: Browser-Local Qwen RAG Optimization for a Rights-Aware Graphic Design Archive

Use this prompt in a new research window to investigate the current bottleneck:
Qwen3.5-0.8B running locally in the browser over a large rights-aware archive
dataset. The goal is to produce a research-grade system plan and paper framing,
not to change product rules directly.

## Project Definition

The project is a rights-aware archive index and research framework for modern
graphic design history. It indexes source-linked objects, texts, sources,
rights states, regions, historical periods, and generated reading surfaces. It
is not an image mirror, not a replacement for source archives, and not a general
chatbot.

The archive assistant should help users read and navigate the archive. It must
not invent historical facts, replace citations, create source evidence, upgrade
image rights, or make unsupported "first" or "most important" claims.

## Fixed Product Constraints

Treat these as fixed unless your report explicitly labels an alternative as a
research-only experiment:

- The only product assistant model identity is `Qwen/Qwen3.5-0.8B`.
- The only product browser runtime artifact is
  `onnx-community/Qwen3.5-0.8B-ONNX`.
- The current frontend runtime path uses Transformers.js / ONNX browser
  execution with the text-only `Qwen3_5ForCausalLM` class.
- No Llama, hosted API fallback, WebLLM catalog fallback, or alternate product
  generation model is allowed.
- Search is deterministic and must remain usable without model load.
- Assistant is not Search. Search returns records; Assistant uses retrieved
  evidence to provide concise advice, caveats, reading routes, and
  conversational orientation.
- AI output is not archive evidence.
- No image download is allowed.
- No image-state or rights upgrade may be inferred from model output.
- IMG03/open-image material may be considered for future stricter multimodal
  experiments; IMG00, IMG01, IMG02, and IMG04 must not be automatically promoted
  into model-image context.

## Local Files To Read First

Start by reading these project files before searching externally:

```text
PROJECT_LOG.md
docs/system/LOCAL_WEBLLM_RAG_FEASIBILITY_v0.md
docs/system/ASSISTANT_RESPONSE_STRATEGY_v0.md
docs/system/WEBGPU_WEBLLM_RAG_RESEARCH_BRANCH_BRIEF_v0.md
frontend/src/lib/qwen35-adapter.ts
frontend/src/lib/assistant-retrieval.ts
frontend/src/components/archive/shell/search.tsx
frontend/scripts/probe-qwen35-runtime.mjs
frontend/scripts/probe-qwen35-generation.mjs
frontend/scripts/probe-qwen35-rag-policy.js
```

If any file has moved, locate it with `rg --files` and record the replacement
path.

## Research Goal

Investigate the system-level problem:

> How can a browser-local Qwen3.5-0.8B assistant answer quickly and usefully
> over a large private/public archive dataset while preserving privacy,
> citation, rights, and evidence constraints?

Do not reduce the problem to raw model speed. Decompose and optimize:

- retrieval;
- candidate filtering;
- graph/topology expansion;
- evidence compression;
- prompt planning;
- tokenization;
- WebGPU runtime initialization;
- model generation;
- memory/session management;
- UI streaming/perceived latency;
- answer evaluation.

## External Research Scope

Research current systems and papers. Prioritize primary sources, official docs,
papers, and project repositories. Use community posts only as practical signals,
clearly labeled as such.

Required source areas:

1. Browser-local inference
   - WebLLM / MLC;
   - Transformers.js;
   - ONNX Runtime WebGPU;
   - WebGPU performance and dispatch overhead;
   - web workers/service workers for inference;
   - browser model caching and cache invalidation.

2. Qwen3.5-0.8B
   - official model card;
   - context length and thinking/non-thinking behavior;
   - ONNX artifact and browser compatibility;
   - known WebGPU/Transformers.js limitations;
   - whether multimodal artifacts are feasible in browser memory.

3. Small-model RAG
   - MiniRAG and graph/topology-aware retrieval;
   - hybrid lexical/semantic retrieval;
   - HyDE and query expansion where appropriate;
   - lightweight reranking;
   - SLM limitations in using retrieved evidence.

4. Latency optimization
   - prompt compression;
   - answer-lane routing;
   - streaming and time-to-first-token;
   - speculative decoding / speculative RAG;
   - distributed/speculative aggregation such as DRAGON, clearly marked if not
     applicable to a browser-only product;
   - KV cache compression and quantization such as KIVI and TurboQuant, clearly
     separating server-GPU results from browser WebGPU feasibility.

5. Evaluation
   - RAG faithfulness metrics;
   - retrieval hit@k / MRR;
   - answer usefulness;
   - refusal correctness;
   - latency metrics such as TTFT, total time, tokens/s, cold/warm load,
     memory/device failures.

## Verification Rules

- Verify the model context length from the Qwen model card and then separately
  verify what the browser runtime artifact can actually handle.
- Do not assume that a server-side optimization applies to WebGPU.
- Do not assume that WebLLM, Transformers.js, and ONNX Runtime expose the same
  cache, worker, quantization, or KV-cache controls.
- Do not treat community speed claims as evidence without local replication.
- Any claim about privacy, local execution, or no server inference must be tied
  to a source or a local code path.
- Any claim about product behavior must be checked against the local repo.

## Required Analysis

### 1. Current Pipeline Map

Map the current frontend assistant path:

- user click;
- panel state;
- retrieval;
- request classification;
- evidence packet;
- prompt construction;
- model loading;
- tokenization;
- generation;
- response rendering;
- memory retention and clearing;
- WebGPU failure handling.

For each step, identify code file, function name, current behavior, likely
latency contribution, and failure mode.

### 2. Bottleneck Decomposition

Produce a table:

| Layer | Current implementation | Suspected bottleneck | How to measure | Likely fix | Risk |
|---|---|---|---|---|---|

Include at least:

- cold model load;
- warm model load;
- retrieval/candidate count;
- prompt bytes and tokens;
- tokenization;
- TTFT;
- total generation time;
- WebGPU memory errors;
- UI rendering/blocking;
- same-page memory.

### 3. Query Taxonomy

Create a query taxonomy for this archive assistant:

- archive orientation;
- current object explanation;
- first/earliest claim;
- period-region recommendation;
- comparison;
- source/rights question;
- method/process question;
- user asks for more context;
- no-evidence or out-of-scope question;
- casual conversational archive help.

For each query type, define:

- retrieval route;
- evidence packet fields;
- max candidates;
- max output tokens;
- target answer length;
- refusal/caveat rule;
- whether Assistant or Research should handle it.

### 4. Retrieval Design

Propose a retrieval stack that works for a 0.8B browser-local model:

- deterministic field/facet filtering;
- keyword/BM25 or lightweight lexical search;
- graph/topology expansion from current main/sub/text/appendix structure;
- optional local embeddings;
- optional lightweight reranker;
- evidence compressor.

Explain why each layer exists and how it avoids turning Assistant into Search.

### 5. Prompt And Evidence Compression

Design prompt templates for:

- fast Assistant;
- longer Research;
- no-evidence refusal;
- archive orientation;
- current object reading;
- "first/earliest" claims;
- region-period recommendations.

Each template must:

- keep Qwen as the final prose generator;
- avoid scripting the final answer;
- include explicit citation/evidence limits;
- prevent fabricated titles, creators, dates, rights, and sources;
- be short enough to test in the browser.

### 6. Runtime And Cache Experiments

Design experiments comparing:

- current Transformers.js WebGPU path;
- ONNX Runtime WebGPU direct path if feasible;
- WebLLM/MLC as a research-only comparison;
- worker vs main-thread inference;
- cold vs warm browser cache;
- service worker / Cache API / immutable model asset serving;
- packaged public model path vs remote artifact;
- session clearing after WebGPU errors.

Do not recommend a runtime switch unless the experiment plan explains migration
cost, product-rule impact, and evidence required.

### 7. Benchmark Harness

Specify a benchmark harness that records:

- query id and query type;
- page/surface context;
- candidate count;
- retrieval time;
- prompt bytes;
- estimated prompt tokens;
- model load time;
- tokenization time;
- TTFT;
- total latency;
- output tokens;
- tokens per second;
- memory/device error;
- answer text;
- source ids used;
- manual quality score.

Define at least 30 benchmark queries, including:

- current object questions;
- "first" questions;
- Russia/France/Latin America/Asia region-period recommendations;
- rights/source questions;
- archive orientation questions;
- no-evidence questions.

### 8. Evaluation Rubric

Create a rubric with scores for:

- faithfulness to retrieved evidence;
- direct usefulness;
- source/citation clarity;
- caveat quality;
- no hallucinated object/source/date/rights;
- answer brevity/completeness;
- next-reading value;
- latency acceptability.

Include separate thresholds for Assistant and Research.

### 9. Paper Framing

Produce a paper framing memo:

- 5 possible titles;
- 1 abstract;
- 3-5 core contributions;
- related work clusters;
- proposed benchmark/dataset description;
- experiment plan;
- limitations;
- ethics/rights section;
- venue fit.

Potential framing:

- browser-local small-model RAG for private archives;
- evidence-packet compression for local 0.8B generation;
- rights-aware visual archive assistants;
- UI-aware answer lanes for local AI;
- WebGPU runtime failure and recovery in archive interfaces.

### 10. Implementation Roadmap

Return a staged plan:

1. measurement instrumentation only;
2. benchmark query set;
3. retrieval and prompt compression;
4. worker/cache/runtime cleanup;
5. answer-quality evaluation;
6. UI integration refinements;
7. paper/demo packaging.

Each stage must list expected files, tests, risks, and project-log entries.

## Required Output Format

Return a structured report with these sections:

1. Executive Summary
2. Current Pipeline Map
3. Annotated Bibliography
4. Bottleneck Decomposition
5. Query Taxonomy
6. Retrieval Architecture Proposal
7. Prompt And Evidence Packet Proposal
8. Runtime Experiment Matrix
9. Benchmark Harness Specification
10. Evaluation Rubric
11. Product-Safe Implementation Roadmap
12. Paper Framing Memo
13. Risks, Non-Goals, And Open Questions

End with:

```text
PRODUCT_RULE_CHANGES_RECOMMENDED: yes/no
RESEARCH_ONLY_RUNTIME_COMPARISONS: ...
FIRST_IMPLEMENTATION_STEP: ...
NEXT_REQUIRED_LOCAL_MEASUREMENT: ...
```

## Hard Boundaries

- Do not write code before producing the research report.
- Do not crawl or download image files.
- Do not push model files into the repository.
- Do not propose hosted inference as the normal product path.
- Do not reintroduce Llama or generic WebLLM model selection into product
  Assistant.
- Do not treat model output as archive evidence.
- Do not claim that a speedup is real until it is measured on the target local
  browser setup.
