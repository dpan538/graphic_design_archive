# Assistant Response Strategy v0

Date: 2026-06-06

## Product Rule

Assistant is not Search.

Search returns matching archive records. Assistant uses local Qwen over a
retrieved evidence brief to make the reading experience better: short guidance,
recommendations, caveats, next checks, and conversational orientation.

The archive assistant has two Qwen-backed modes:

1. Assistant
2. Research

Assistant is the fast RAG mode. It should target a short answer, usually around
80-120 characters when the question allows it. It may take longer on cold model
load, but the answer itself must still come from Qwen, not from a scripted
search-result template. Retrieval scripts prepare evidence; they do not pretend
to be the assistant.

Research is the longer RAG mode. It may use broader evidence and a more
developed answer structure for relationship mapping, interpretation, and
research planning.

## Runtime Rule

- `Qwen/Qwen3.5-0.8B` is the only model identity.
- `onnx-community/Qwen3.5-0.8B-ONNX` is the only frontend runtime artifact.
- No Llama, hosted API, WebLLM catalog fallback, or alternate local generation
  model is permitted.
- Search must remain deterministic and usable without model load.
- Assistant may prewarm Qwen after the panel opens.
- If Qwen is cold, the UI may show a temporary preparation notice after about 3
  seconds, but it must replace that notice with a Qwen answer once ready.
- Until packaged model assets are added under a documented public model path,
  the browser runtime must not probe `/models/`; it should load the approved
  `onnx-community/Qwen3.5-0.8B-ONNX` artifact with browser cache.

## RAG Contract

Retrieval provides:

- active surface or folder context;
- candidate records;
- date/region/source/image-state evidence;
- source links and rights labels when available;
- compact notes only, not long raw text.
- a scripted request plan that classifies the user's task and composes a short
  answer directive for Qwen.

The scripted request plan may classify intent, focus terms, answer shape, and
evidence policy. It must not be treated as the final answer. It exists only to
make the RAG prompt shorter, faster, and more useful.

Qwen provides:

- a conversational answer;
- a recommendation or caveat when useful;
- a next reading move when the question is exploratory;
- a short explanation of evidence limits when the archive does not support the
  requested claim.

Qwen must not:

- invent titles, creators, dates, citations, or rights states;
- answer by merely restating the active folder;
- output engineering phrases such as `is indexed here`, `reading angle`, or
  `current context`;
- list many records unless the user asks for a list;
- treat a current-archive ranking as an objective historical canon.

## Tone

The assistant should sound like a concise archive research aide:

- direct;
- human;
- curious but not verbose;
- grounded in the current archive evidence;
- willing to say when evidence is weak;
- useful even when the answer is provisional.

Examples of the intended shape:

- `Start with SURF-...; it is the strongest current archive candidate, but verify the source date before treating it as "first".`
- `The archive does not show a strong 1970 Russia artwork candidate here; broaden to 1970s posters or Soviet visual communication.`
- `This archive is a rights-aware graphic design index: use folders for routes, surfaces for source evidence, and Assistant for reading choices.`

## Implementation Binding

- `frontend/src/lib/assistant-retrieval.ts` owns deterministic candidate
  retrieval, request classification, prompt-brief composition, and evidence
  compression.
- `frontend/src/lib/qwen35-adapter.ts` owns Qwen prompt mode, answer length, and
  local model runtime binding.
- `frontend/src/components/archive/shell/search.tsx` sends normal Assistant
  questions through Qwen fast mode and Research questions through Qwen research
  mode.
- No scripted ordinary-answer module should be used as the final Assistant
  response layer.

## LoRA / Fine-Tuning Position

Do not introduce LoRA or fine-tuned browser adapters for the next product pass.
The current failures are primarily RAG orchestration failures: overly broad or
weak evidence, insufficient prompt contract, no stable quality fixtures, and
missing latency decomposition.

Before any fine-tuning is considered, the project must first collect a reviewed
answer fixture set containing:

- user question;
- retrieved evidence packet;
- model answer;
- preferred answer;
- failure label;
- latency and token metrics.

LoRA may be reconsidered only if prompt/RAG/few-shot controls still fail after
that fixture set exists and the added model files, browser cache cost, WebGPU
memory pressure, and reproducibility risks are measured. Any LoRA work belongs
in a research branch first, not in the product Assistant path.

## Development Timing Rule

Assistant optimization should be measurement-first. Development builds may log
per-question timings for retrieval, model preparation, tokenization,
generation, total answer time, prompt size, and token counts. These logs are
diagnostic only and must not become visible archive UI chrome.
