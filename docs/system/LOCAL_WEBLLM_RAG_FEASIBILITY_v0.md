# Local Multimodal RAG Integration v0

Date: 2026-06-03

## Decision Summary

The archive assistant should be a local multimodal retrieval assistant, not a
general chatbot. First-version integration uses Qwen3.5-0.8B directly as the
only answer-generation model.

It should answer only from the project's public payload, methodology/docs,
source registry, rights notes, generated dossier structure, and image inputs
that are permitted by the archive's image-state policy. It must not call a
remote LLM API and must not use AI output as archival evidence.

Recommended v0 stack:

1. Transformers.js for local embeddings and optional reranking.
2. A static build-time vector index over archive chunks.
3. Qwen3.5-0.8B as the first-version multimodal local-generation model,
   lazy-loaded only when the user opens the assistant.
4. Keyword/facet search remains the non-AI search interface, not an LLM
   fallback path.

This keeps the system aligned with the project method: search and synthesis are
navigation aids over cited archive records, not new historical authority.

## Fixed First-Version Components

| Candidate | Role | Locality | Strength | Main Risk | Fit |
|---|---|---|---|---|---|
| Qwen3.5-0.8B | Multimodal answer generation | Local/browser target to be validated through WebGPU-capable runtime | Native image-text-to-text scale fit for a visual archive | Runtime benchmark and image-rights gating | Required first-version model |
| WebGPU runtime layer | Browser-local model execution | Browser-local, no server inference | Keeps assistant local and aligned with project constraints | Must confirm packaging path for Qwen3.5-0.8B | Required runtime workstream |
| Transformers.js | Embeddings, similarity, small classifiers, optional extraction | Browser-local ONNX/WASM/WebGPU; can load local model assets | Strong fit for feature extraction, sentence similarity, quantized models, browser cache controls | Not ideal as the main prose generator for nuanced answers | Best retrieval layer |

## Model Decision

Qwen3.5-0.8B is the selected first-version model. Smaller text-only Qwen
models are not implementation fallbacks. They may appear only in historical
notes or future benchmarking records.

The first benchmark should measure Qwen3.5-0.8B only:

- local load time;
- cached reload time;
- memory pressure;
- answer faithfulness against retrieved chunks;
- refusal behavior when no cited archive evidence is retrieved;
- behavior with IMG00, IMG01, IMG02, IMG03, and IMG04 records;
- whether image input is correctly suppressed when rights state forbids local
  image use.

Sources checked:

- WebLLM official docs state that it runs model inference in the browser and
  needs a WebGPU-compatible browser. It is installable as `@mlc-ai/web-llm`.
  <https://webllm.mlc.ai/docs/user/get_started.html>
- WebLLM GitHub states that it runs without server-side processing, uses
  WebGPU, has OpenAI API compatibility, supports workers, and supports model
  families including Llama, Phi, Gemma, Mistral, and Qwen.
  <https://github.com/mlc-ai/web-llm>
- Qwen3.5-0.8B's official Hugging Face model page identifies it as an
  image-text-to-text model, provides image-text examples through Transformers,
  and lists an Apache-2.0 license.
  <https://huggingface.co/Qwen/Qwen3.5-0.8B>
- NVIDIA's Qwen 3.5 VLM documentation lists Qwen3.5-0.8B as a 0.8B
  vision-language model supporting multimodal understanding.
  <https://docs.nvidia.com/nemo/megatron-bridge/latest/models/vlm/qwen35-vl.html>
- AWS describes Qwen3.5-0.8B as a compact multimodal model for rapid
  prototyping, on-device inference, and edge deployments.
  <https://aws.amazon.com/about-aws/whats-new/2026/05/qwen-models-on-sagemaker-jumpstart/>
- Transformers.js official docs state that it runs Transformers in the browser
  with no server, uses ONNX Runtime, supports quantized dtypes, and supports
  feature extraction and sentence similarity.
  <https://huggingface.co/docs/transformers.js/>
- Transformers.js environment docs expose controls for local model loading,
  remote model blocking, browser cache, local model path, and WASM caching.
  <https://huggingface.co/docs/transformers.js/main/api/env>
- Wllama states that it runs LLM inference in the browser using WebAssembly and
  WebGPU and accepts GGUF, but warns about performance and memory limits.
  <https://reeselevine.github.io/wllama/>
- Chrome's AI model caching guidance recommends explicit on-device caching and
  long-lived immutable cache headers for model files served with the app.
  <https://developer.chrome.com/docs/ai/cache-models>

Binding clarification after 2026-06-06 assistant correction:

- The model-family comparison above is background research only. It does not
  authorize a Llama, WebLLM catalog, Wllama, hosted API, or other fallback
  runtime in the product assistant.
- Product assistant generation is bound to `Qwen/Qwen3.5-0.8B` only, using
  `onnx-community/Qwen3.5-0.8B-ONNX` as the runtime artifact.

## First Runtime Probe

Date: 2026-06-03

Probe scripts:

- `frontend/scripts/probe-qwen35-rag-policy.js`
- `frontend/scripts/probe-qwen35-runtime.mjs`

Result:

- Transformers.js imported successfully in the local project runtime.
- `Qwen/Qwen3.5-0.8B` remains the selected model identity, but the raw Hugging
  Face model repository is not directly loadable by the browser runtime because
  it does not provide the required quantized ONNX files for Transformers.js.
- `onnx-community/Qwen3.5-0.8B-ONNX` is the required runtime artifact for the
  same model choice in this implementation path.
- The direct base-repository probe failed while looking for
  `onnx/embed_tokens_q4.onnx`.
- The ONNX artifact initially exposed a Node external-data path issue. The probe
  was corrected to pass `externalData` explicitly.
- The corrected probe loaded `Qwen3_5ForConditionalGeneration` successfully in
  Node through Transformers.js, with local cache enabled. The measured load time
  for the first successful local probe was about 7.9 seconds after model files
  were present.

Image-context policy probe:

- Current public payload image-state counts:
  - IMG00: 41
  - IMG01: 37
  - IMG02: 733
  - IMG03: 481
  - IMG04: 125
- Conservative v0 model-image input eligibility: 481 records.
- Only `IMG03` records with `open_image_frame` are eligible to pass image pixels
  into the local multimodal model.
- `IMG00` is always metadata/source-link only.
- `IMG01` and `IMG02` may be visible in the public interface, but are withheld
  from model-image context until a stricter rights rule explicitly permits
  local model use.
- `IMG04` is text-only and has no image field.

Implementation consequence:

Model choice and runtime artifact must be named separately:

- model identity: `Qwen/Qwen3.5-0.8B`;
- local runtime artifact: `onnx-community/Qwen3.5-0.8B-ONNX`;
- no alternate generation model in v0.

The `.model-cache/` directory is local-only and ignored by Git. Model files
must never be pushed as accidental source assets.

## Second Generation Probe

Date: 2026-06-03

Probe script:

- `frontend/scripts/probe-qwen35-generation.mjs`

Result:

- The local model can generate an archive answer from a supplied surface
  context.
- Cached local load improved to about 3.9 seconds in the second probe.
- One constrained evidence answer still took about 48 seconds in the Node/CPU
  probe. The browser implementation must therefore be lazy-loaded, streamed,
  and used only for explicit assistant questions rather than ordinary search.
- The first no-evidence test proved that prompt instructions alone are not a
  sufficient guardrail: the model hallucinated when asked about a topic absent
  from the supplied context.
- The probe was corrected so no-evidence questions are blocked by retrieval
  gate before model invocation. The corrected no-evidence path returns a direct
  archive-limited refusal in 0 ms and does not call the model.

Required product rule:

The assistant must not call Qwen3.5-0.8B unless retrieval has produced at least
one cited eligible chunk. Prompt wording is a secondary guardrail, not the
primary safety mechanism.

Known output issues:

- The model can emit hidden-reasoning tags or repeat part of the answer in raw
  text-generation mode. UI integration must sanitize these tokens and should
  prefer a proper chat-template path when the browser implementation is wired.
- The current Node/CPU timing is too slow for search. Use keyword/facet search
  as the instant layer and Qwen only as a deliberate synthesis layer.

## Search-Integrated Micro-Answer Probe

Date: 2026-06-03

The first 48-second answer was too slow for a public search experience. A second
round tested whether Qwen3.5-0.8B can sit inside ordinary search if the archive
gives it a compact contract instead of long context.

Observed failures:

- Long archive context produced slow answers.
- Prompt-only no-evidence refusal failed and hallucinated.
- Very short `max_new_tokens` settings produced incomplete answers.
- Search-result synthesis became unreliable when the model was asked to provide
  the full factual result row itself.

Final tested shape:

- DB/search returns deterministic result rows: title, date, surface id, source,
  source URL, image state, and verification action.
- Qwen receives only a compact record slip or top-hit slip.
- Qwen generates only an optional micro-note / reading angle.
- The retrieval gate refuses without calling Qwen when no cited chunk exists.

Final Node/CPU probe timings:

- cached model load: about 4.1 seconds;
- record micro-note: about 11.8 seconds;
- search micro-note: about 14.0 seconds;
- no-evidence refusal: 0 seconds because the model is not called.

Product conclusion:

Qwen3.5-0.8B can partially augment ordinary search, but it should not replace
ordinary search. It belongs inside search as a local optional explanation layer:
deterministic records first, generated reading angle second. If the generated
micro-note is incomplete, missing a citation surface, or contradicts the
deterministic row, the UI should suppress it.

Generated text must never update database records, source descriptions, rights
states, folder membership, or archive classifications.

## RAG Corpus Boundary

Allowed corpus:

- `generated/public_surfaces_v1.json`
- `frontend/src/data/public_surface_mock_v0.json` after release freeze
- methodology/system/capture docs
- source registry and source coverage docs
- rights/image state notes
- dossier page sequence metadata
- short source-derived excerpts already accepted into the project

Disallowed corpus:

- raw copyrighted books, articles, catalogue essays, or long OCR text copied
  into the project without a rights basis;
- remote web pages fetched live during a user query;
- model-generated descriptions treated as evidence;
- image pixels used as hidden evidence unless the image itself is already
  permitted under the project's image policy.

## Chunking Contract

Each chunk should be source-addressable. A good chunk has:

- `chunk_id`
- `surface_id` or `folder_id` or `dossier_id`
- `page_type`
- `title`
- `date_start`, `date_end`
- `folder_refs`
- `source_name`
- `source_url`
- `rights_state`
- `image_state`
- `text`
- `citation_hint`

Do not create free-floating narrative chunks. If a retrieved passage cannot
point back to a surface, source, folder, or methodology file, it should not be
eligible for assistant answers.

## Multimodal Retrieval Flow

1. User asks a question in the archive assistant.
2. Query is normalized locally.
3. Keyword/facet filter narrows by date, folder type, region, movement, medium,
   source, rights state, or image state when explicit.
4. Local embedding search retrieves top candidate chunks.
5. Optional lightweight rerank reorders candidates by exact term overlap,
   folder match, date match, source quality, and rights visibility.
6. Image inputs are selected only from rights-permitted records:
   - IMG00: no image input;
   - IMG01/IMG02/IMG03: image input allowed only if the specific image policy
     permits local model context;
   - IMG04: no image input because the page has no image field.
7. Qwen3.5-0.8B receives selected chunks, permitted image inputs, and a strict
   system instruction: answer only from supplied archive context.
8. The answer returns citations as surface/folder/source links. If evidence is
   weak or absent, the assistant says the archive does not currently contain
   enough evidence.

## Copyright Guardrails

- The assistant may summarize project-owned normalized metadata and our own
  methodology text.
- The assistant may inspect only images that the project is allowed to place
  into local model context.
- IMG00 images are never fetched or shown to the model. Their blankness is
  evidence of the display decision.
- For source text, it should quote only short excerpts already present in the
  project payload, and should prefer paraphrase with citation.
- It must not reconstruct catalogue essays, book passages, OCR pages, or
  institution descriptions.
- It must show source-return links as primary evidence.
- It must not imply that source-held images or objects belong to the project.
- It must never use AI-generated text as proof of historical fact. Generated
  text is an access layer over cited chunks.

## Performance Strategy

Qwen3.5-0.8B and embedding models should not load on initial page view.

Recommended behavior:

- load keyword search immediately;
- load embeddings only after the user opens the assistant or asks semantic
  search;
- load Qwen3.5-0.8B only after the user asks for an answer, not for ordinary
  search;
- keep vector index static and compressed;
- cache model files explicitly in browser storage;
- set model assets to long-lived immutable cache headers if served locally;
- keep ordinary search usable without loading the model.

Model weights should not be committed accidentally as ordinary source files.
If bundled, they should live in a documented model asset path or release asset
workflow with checksum/integrity metadata. This is both a performance issue and
a repository hygiene issue.

## Recommended v0 Implementation

Build-time:

- `scripts/build_rag_chunks_v1.py`
  - reads public payload and selected docs;
  - writes `generated/rag_chunks_v1.jsonl`;
  - excludes raw copyrighted long text;
  - tags every chunk with rights/source/dossier ids.
- `scripts/build_rag_index_v1.ts` or Python equivalent
  - creates embeddings;
  - writes `frontend/public/data/rag_index_v1.json` or binary shard;
  - writes `frontend/public/data/rag_chunks_v1.json`.

Frontend:

- `LocalArchiveAssistant`
  - disabled by default;
  - loads retrieval index lazily;
  - loads Qwen3.5-0.8B lazily;
  - shows cited retrieved chunks before or beside generated answer;
  - shows whether image context was passed or suppressed;
  - keeps "View at source" links visible;
  - includes "answer limited to archive data" label.

Generation:

- Model: Qwen3.5-0.8B.
- Retrieval: Transformers.js feature extraction model.
- No alternate generation model in v0.

## Open Questions

- Whether to ship the model directly in the repo or as a release/static asset
  needs a size policy. The GitHub secret alert incident already shows that
  repository hygiene must be explicit.
- The assistant should be blocked from answering if no cited chunks are
  retrieved. This is more important than fluency.
- The runtime packaging path for Qwen3.5-0.8B must be validated before wiring
  the UI. Model choice is fixed; runtime implementation is the remaining risk.
