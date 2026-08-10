# 08 — AI / RAG / SLM Runtime and Retirement Audit

- Audit package: **A8**
- Audit date: **2026-08-11 (Australia/Brisbane)**
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Baseline commit: `f076ca3444aaa0f413bb61fe2cb568d6a9aa2720`
- Protected worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history` (read-only)
- Coverage: **COMPLETE** for the A8 boundary
- Result: **PARTIAL**

`PARTIAL` is a retirement-readiness result, not a scan-coverage result. The v49
checkout still imports and exposes a browser-local Qwen assistant, and its
package lock still carries the model runtime. No AI source or dependency was
removed because frontend and package files are outside this task's edit
allowlist. The active path is a **frontend-promotion P0**, but it does not by
itself alter the identity/cardinality decisions needed to draft physical DDL.

## 1. Scope

This package inspected:

- tracked v49 frontend source, package scripts, dependency lock, direct probe
  runners, generated probe outputs, prompts, AI/RAG system notes, and generated
  Deep Research reports;
- names and non-secret runtime markers for OpenAI, Anthropic, hosted model APIs,
  Hugging Face/Transformers.js, WebLLM, Qwen, ONNX Runtime, LangChain,
  LlamaIndex, embeddings, vector indexes, retrievers, rerankers, agents, and
  model weights;
- the executable chain from the reader's Assistant control through evidence
  retrieval and local generation;
- package/build/browser entrypoints relevant to accidentally restarting the old
  AI or bulk-generation path (with the complete A4/static-render audit owned by
  [A7](07_FRONTEND_A4_AND_BUILD_COUPLING.md));
- all protected-main AI paths identified in the outer untracked population,
  including `Archive/AI/`, two independent nested research repositories, and
  two Browser-Local Qwen report artifacts;
- environment/credential filenames without reading or printing secret values;
- an argument-redacted process inventory. No process was killed.

The retirement ledger uses a **logical path unit**. An independent nested Git
repository counts once in the four-way retirement total; its internal file
count is reported separately so 892 internal tracked files are not mixed with
outer-repository path units.

## 2. Evidence commands

All commands were read-only except creation of this report. Searches that could
encounter credentials returned filenames or variable-name patterns only; no
secret value or process argument was printed.

```sh
repo=/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform
main=/Users/jarlgiovanni/Desktop/modern_GD_history

git -C "$repo" status --short --branch
git -C "$repo" rev-parse HEAD
git -C "$repo" ls-files
git -C "$repo" ls-files prompts reports frontend/scripts generated

rg -l -i \
  '(@huggingface/transformers|openai|anthropic|langchain|llamaindex|webllm|qwen3|onnxruntime|embedding|vector (index|store|search)|faiss|chroma|pinecone|weaviate|qdrant|milvus|pgvector|retriever|rerank)' \
  frontend/src frontend/scripts scripts db \
  --glob '*.{ts,tsx,js,jsx,mjs,cjs,py,sh,sql,md,json}'

rg -l -i 'assistant' frontend/src \
  --glob '*.{ts,tsx,js,jsx,mjs,cjs,css,scss}'
rg -n -i \
  'qwen35-adapter|createQwenAssistantSession|archive-assistant-evidence|assistant-memory' \
  frontend/src

sed -n '1,260p' frontend/package.json
sed -n '1,440p' frontend/src/lib/qwen35-adapter.ts
sed -n '1,760p' frontend/src/components/archive/shell/search.tsx
sed -n '1,320p' frontend/src/app/api/archive-assistant-evidence/route.ts
sed -n '1,320p' frontend/src/lib/assistant-memory.ts
sed -n '1,520p' frontend/src/lib/assistant-retrieval.ts

rg -n \
  'node_modules/@huggingface/transformers|node_modules/onnxruntime|"@huggingface/transformers"' \
  frontend/package.json frontend/package-lock.json
rg -n 'generateStaticParams' frontend/src frontend/scripts
rg -n -i \
  'puppeteer|playwright|launch\(|screenshot|page\.pdf|printToPDF' \
  frontend/scripts

find . -path './.git' -prune -o -type f \
  \( -name '.env' -o -name '.env.*' -o -name '*.env' \
     -o -name '*.pem' -o -name '*.key' -o -iname '*credentials*' \) -print
find . -maxdepth 2 -type d -print
du -sh .model-cache frontend/.model-cache frontend/node_modules \
  frontend/.next  # each candidate was absent

jq \
  '{generatedAt,result,baseModelTarget,runtimeModelTarget,modelTarget,summary,counts,modelImageInputEligible,payloadShape}' \
  generated/archive_assistant_primer_v0.json \
  generated/qwen35_generation_probe_v0.json \
  generated/qwen35_rag_policy_probe_v0.json \
  generated/qwen35_runtime_probe_v0.json
shasum -a 256 frontend/scripts/probe-qwen35-* generated/qwen35_* \
  generated/archive_assistant_primer_v0.json

git -C "$main" ls-files --others --exclude-standard
find "$main/Archive/AI" -maxdepth 4 -print
cmp -s <v49-path> <protected-main-archive-copy>

git -C "$main/research-repo/browser-local-hybrid-rag-lanes" \
  status --short --branch
git -C "$main/research-repo/browser-local-rag-lab" \
  status --short --branch
git -C <nested-repo> ls-files
git -C <nested-repo> ls-files --others --exclude-standard
du -sh <nested-repo> <nested-repo>/*
find <nested-repo> -path '*/.git' -prune \
  -o -path '*/node_modules' -prune \
  -o -type f \
  \( -iname '*.onnx' -o -iname '*.onnx_data' -o -iname '*.gguf' \
     -o -iname '*.safetensors' -o -iname '*.pt' -o -iname '*.pth' \
     -o -iname '*.ckpt' \) -print

# Process arguments were deliberately omitted.
ps -axo pid=,ppid=,etime=,ucomm=
lsof -a -p <pid> -d cwd -Fn
lsof -nP -a -p <pid> -iTCP -sTCP:LISTEN
```

The first sandboxed `ps` attempt returned `operation not permitted`. The same
read-only, argument-redacted query was then run with approved read permission.
It did not inspect environment blocks or command arguments.

## 3. Measured result summary

| Measurement | Result | Status |
| --- | ---: | --- |
| Tracked files at baseline | 3,419 | context |
| v49 AI paths requiring removal/edit before frontend promotion | 10 | FAIL (retirement) |
| v49 tracked probe runners and generated probe artifacts | 7 | PARTIAL |
| v49 AI/Deep Research documentation paths retained as history | 42 | PASS (classified) |
| Protected-main logical AI units | 16 | PARTIAL |
| Nested research repos, internally tracked files | 2 repos / 892 files | context; not added to logical total |
| Model SDKs in v49 runtime | 1 direct (`@huggingface/transformers`) | measured |
| Hosted generation SDKs or endpoints | 0 | PASS |
| Implemented embedding/vector indexes in v49 | 0 | PASS (absence established) |
| Model-weight files in v49 checkout | 0 | PASS |
| v49 `.model-cache`, `node_modules`, `.next` | all absent | PASS |
| v49 env/credential-like files found by filename | 0 | PASS |
| Docker/Compose or top-level workflow files found by bounded A8 scan | 0 | PASS (A10 owns global gate) |
| Task-owned model/server/build/browser/database processes | 0 | PASS |

## 4. Active v49 runtime chain

The assistant is not dormant documentation. It is wired into the current v49
frontend:

```text
Reader Assistant button
  -> window CustomEvent("archive:open-assistant")
  -> ArchiveShell switches SearchBox to assistant mode
  -> SearchBox schedules prepareQwen() after 250 ms
  -> dynamic import of qwen35-adapter
  -> @huggingface/transformers loads remote ONNX artifact into browser cache
  -> WebGPU local generation

question submit
  -> POST /api/archive-assistant-evidence
  -> deterministic assistant-retrieval over archive-data
  -> compact evidence and request plan returned to browser
  -> Qwen prompt + evidence + bounded session history
  -> locally generated answer
```

This establishes four important facts:

1. Opening Assistant is sufficient to start model preparation. The code's
   250 ms effect does not wait for the first submitted question, despite older
   documentation describing first-question lazy loading.
2. `qwen35-adapter.ts` sets `allowRemoteModels=true`,
   `allowLocalModels=false`, and `useBrowserCache=true`; the selected artifact
   is `onnx-community/Qwen3.5-0.8B-ONNX` and generation uses WebGPU.
3. The evidence layer is deterministic lexical/field ranking. No embedding
   model, vector store, FAISS/Chroma/Pinecone/Qdrant/pgvector index, semantic
   reranker, LangChain, or LlamaIndex implementation exists in tracked v49.
4. The generation is browser-local, not a hosted OpenAI/Anthropic call. Remote
   network activity is nevertheless required to acquire model artifacts, and
   the artifact is cached in the browser.

Assistant memory stores up to 12 messages per page in `sessionStorage`, with a
three-minute TTL and a three-page-switch reset policy. This is short-lived but
is still a separate privacy/runtime state that the deterministic archive does
not need.

### Affected runtime paths (10)

| Path or path family | Current role | Retirement action | Recovery reference |
| --- | --- | --- | --- |
| `frontend/src/components/archive/reader/Reader.tsx` | emits assistant-open event and renders launcher | remove assistant-only control/event; retain reader | baseline Git object; protected `Archive/AI/product-prototype/Reader.tsx` is byte-identical |
| `frontend/src/components/archive/shell/ArchiveShell.tsx` | assistant mode/context state | remove assistant mode while preserving deterministic Search | baseline Git object; protected archive copy exists but differs |
| `frontend/src/components/archive/shell/search.tsx` | mixed deterministic Search and Qwen chat | split/retain Search; remove assistant branch | baseline Git object; protected archive copy exists but differs |
| `frontend/src/app/api/archive-assistant-evidence/route.ts` | unauthenticated internal POST evidence planner | remove from runtime; preserve source in history if needed | baseline Git object |
| `frontend/src/lib/assistant-memory.ts` | browser message state | remove from runtime | byte-identical protected archive copy |
| `frontend/src/lib/assistant-retrieval.ts` | deterministic RAG evidence planner | remove from product runtime or preserve as research-only algorithm | byte-identical protected archive copy |
| `frontend/src/lib/qwen35-adapter.ts` | remote model acquisition and WebGPU generation | remove from product runtime | baseline Git object; protected archive copy exists but differs |
| `frontend/src/app/globals.css` | assistant-only CSS mixed with active styles | remove only proven assistant selectors in a frontend-authorized change | baseline Git object |
| `frontend/package.json` | direct Transformers.js dependency | remove dependency only after runtime imports are removed | baseline Git object |
| `frontend/package-lock.json` | locks HF/ONNX runtime graph | regenerate through authorized dependency workflow | baseline Git object |

The protected dirty main currently contains no working-tree references to the
Hugging Face/Qwen assistant path and no corresponding package dependency. That
is evidence of a later retirement attempt, **not** an authority source: the
dirty main cannot be cherry-picked or copied wholesale, and its archive is
untracked. A clean, reviewed frontend cleanup must reproduce the intended
boundary from this ledger.

## 5. Dependency and executable-entrypoint inventory

### 5.1 Model dependency graph

- `frontend/package.json` directly declares
  `@huggingface/transformers` at `^4.2.0`.
- `frontend/package-lock.json` resolves that package and transitively carries
  `onnxruntime-node` `1.24.3`, `onnxruntime-web`
  `1.26.0-dev.20260416-b7804b056c`, and corresponding
  `onnxruntime-common` entries.
- No OpenAI, Anthropic, LangChain, LlamaIndex, WebLLM package, Python model
  package, hosted inference client, or vector database dependency was found in
  the v49 project manifest.
- No package script invokes the Qwen probes. They remain directly executable
  Node entrypoints and therefore can still download/load model artifacts if a
  person runs them manually.

### 5.2 Explicit process/build/generator entrypoints

`frontend/package.json` has 17 scripts:

- 7 Next lifecycle entries: one full `next build`, one `next start`, one
  general `next dev`, and four additional `next dev` preview ports;
- 4 package-bound Puppeteer capture entries;
- 3 Node verification entries;
- 1 browser asset/a11y entry;
- 1 archive-search data generator; and
- 1 Next lint entry.

There are 13 tracked files in `frontend/scripts/`: three Qwen probes, five
Puppeteer capture scripts (including the direct-only `capture-file-page.js`),
three visual verification scripts, one asset/a11y script, and one Search index
generator. Two route modules export `generateStaticParams`:

- `frontend/src/app/folders/[type]/page.tsx`;
- `frontend/src/app/trace/types/[type]/page.tsx`.

A8 found no explicit package script named A4, PDF, print, export, or full-site
surface generation. That negative result does not replace A7's route/data-load
analysis. The authoritative A4/static/build counts and retirement boundary are
in [07_FRONTEND_A4_AND_BUILD_COUPLING.md](07_FRONTEND_A4_AND_BUILD_COUPLING.md).

### 5.3 Direct AI probe entrypoints and outputs

| Runner | Output | Finding | Classification |
| --- | --- | --- | --- |
| `frontend/scripts/probe-qwen35-runtime.mjs` | `generated/qwen35_runtime_probe_v0.json` | can run metadata mode or acquire/load remote model in `--mode=load`; recorded `model_load_ok` | `ARCHIVE_READ_ONLY` after removal from runtime tree |
| `frontend/scripts/probe-qwen35-generation.mjs` | `generated/qwen35_generation_probe_v0.json` and primer | acquires Qwen tokenizer/model and writes reports/cache; recorded `generation_probe_ok` | `ARCHIVE_READ_ONLY` |
| `frontend/scripts/probe-qwen35-rag-policy.js` | `generated/qwen35_rag_policy_probe_v0.json` | does not call model but writes a policy sample | `ARCHIVE_READ_ONLY` |

The four output JSON files were generated on 2026-06-03 from a payload of only
**1,417 surfaces**, not the frozen 15,923 canonical/TRACE population. The policy
output reports 481 model-image-eligible records under its old IMG03 rule. These
are experiment receipts, not v48 parity evidence and not v49 migration input.
They also embed absolute paths into the protected main, confirming their
machine-local provenance.

## 6. Retirement ledger

### 6.1 Count contract

| Retirement class | Logical units | Included population | Decision |
| --- | ---: | --- | --- |
| **remove from runtime** | **10** | eight active frontend source/style paths plus two package files | mandatory before frontend promotion |
| **archive for history** | **22** | 7 v49 probe/output paths; 12 protected `Archive/AI` files; 2 protected report artifacts; 1 clean nested research repo | preserve outside product runtime |
| **keep as documentation** | **42** | 11 `prompts/` paths, 28 `reports/` paths, 3 AI/RAG system docs | retain with historical/non-authoritative status |
| **unknown / needs review** | **1** | dirty nested `browser-local-rag-lab` repository | owner/freeze decision required |
| **Total** | **75** | logical path units | nested repo internals excluded by contract |

### 6.2 Archive-for-history details

The 12 files under protected-main `Archive/AI/` consist of an archive README,
three probe runners, six product-prototype source files, and two research notes.
The README labels the set frozen on 2026-07-28 and states that the active product
retains deterministic Search only. Of 11 comparable files, seven are
byte-identical to v49 and four differ (`qwen35-adapter.ts`, `search.tsx`,
`ArchiveShell.tsx`, and the WebGPU research brief). The archive is therefore a
useful recovery reference, not a byte-for-byte retirement recipe.

The two additional protected-main report artifacts are:

- `reports/deep-research/Browser-Local Qwen RAG Optimization for a Rights-Aware Graphic Design Archive.docx` (Microsoft OOXML, 34,086 bytes);
- `reports/deep-research/Browser-Local Qwen RAG Optim.textClipping` (Apple binary property list, 484 bytes).

The `.textClipping` is non-portable Finder metadata/evidence and should be
considered a later deletion candidate only after the DOCX and its provenance
are frozen; it was not deleted here.

### 6.3 Independent research repositories

| Protected-main nested repo | HEAD / state | Measured storage | Model weights | Retirement decision |
| --- | --- | ---: | ---: | --- |
| `research-repo/browser-local-hybrid-rag-lanes/` | `75b375c…`, clean, 213 tracked, 0 non-ignored untracked | 33 MiB, including 22 MiB `.venv` | 0 outside dependency/cache exclusions | archive as independent research repo; never promote into product runtime |
| `research-repo/browser-local-rag-lab/` | `b82d897…`, 9 modified tracked reports, 679 tracked, 0 non-ignored untracked | 6.9 GiB, dominated by 6.9 GiB `node_modules` | 0 outside `node_modules` | `HOLD_UNKNOWN`; owner must decide whether modifications are evidence before freeze |

Together they contain 892 internally tracked files. That number is context,
not 892 additional outer-ledger entries. The first repo contains a Flask app,
Python experiment runners, a Qwen/WebLLM browser panel, schemas, fixtures, and
reports. The second contains browser labs, many Node benchmark/evaluation
runners, fixtures, prompts, reports, and model-comparison results. They are
independent research workspaces and must not be imported as v49 application
dependencies.

The 6.9 GiB `node_modules` tree is a future reversible `DELETE_CANDIDATE` with
lockfile-based recovery, but protected-main cleanup is prohibited in this task.
The clean repo's 22 MiB `.venv` is the same kind of generated dependency tree.
Neither was removed or modified.

### 6.4 Keep-as-documentation details

- All 11 paths under `prompts/` are prompt history, including the README and
  the browser-local RAG optimization prompt. A prompt does not authorize a run,
  crawl, ingest, or claim.
- All 28 paths under `reports/` are generated Deep Research report history or
  its README. They are inputs to human methodology review, not canonical data,
  not source evidence by themselves, and not executable instructions.
- `docs/system/LOCAL_WEBLLM_RAG_FEASIBILITY_v0.md`,
  `docs/system/WEBGPU_WEBLLM_RAG_RESEARCH_BRANCH_BRIEF_v0.md`, and
  `docs/system/ASSISTANT_RESPONSE_STRATEGY_v0.md` preserve product/research
  decisions. They should receive an explicit historical/retired banner in the
  later cleanup change; this audit did not alter them.

## 7. Environment, secrets, weights, and runtime-state risk

- No `.env`, `.env.*`, `*.env`, credential-named file, private key, or model
  weight was found in the v49 worktree by the bounded A8 filename scan.
- The nested research repos contained no environment file. The only PEM match
  was the standard certifi CA bundle inside a Python virtual environment; it is
  not a project credential.
- No environment value, token, process argument, `.git/config` credential, or
  secret payload was printed. `scripts/audit_secret_patterns.py` contains an
  OpenAI-key regex; the regex is a defensive detector, not evidence of a key.
- No tracked v49 `.model-cache`, `frontend/node_modules`, or `frontend/.next`
  exists. No ONNX, GGUF, SafeTensors, PyTorch checkpoint, or similar model
  weight was found in the v49 checkout.
- Remote model acquisition remains enabled in source. This is a dependency
  integrity, bandwidth, browser-cache, and reproducibility risk even though
  generation is local and no hosted inference credential is used.
- The internal assistant evidence route is POST and has no explicit auth or
  rate-limiting boundary. It does not itself call a model, but it should be
  removed with the assistant rather than mistaken for the future GET-only Read
  API.

## 8. Process receipt

The argument-redacted process scan observed:

| Process class | Count | Classification |
| --- | ---: | --- |
| Node | 6 | pre-existing; none has v49 worktree cwd |
| PostgreSQL | 6 | one long-running parent plus five workers, about 20 days old |
| Next/TypeScript compiler by executable name | 0 | none detected |
| Docker | 0 | none detected |
| Playwright/Puppeteer/browser driver | 0 | none detected |
| A8-owned shell/model/service process | 0 | PASS |

Three Node processes had cwd under protected main and three under
`/Users/jarlgiovanni/Desktop/words_overtime`. The protected-main Node processes
were sleeping, at 0.0% CPU when sampled, had parent PID 1, were between roughly
9.5 hours and 5.5 days old, and exposed no listening TCP socket in the bounded
`lsof` check. They predate A8 and were not started, killed, or adopted by this
task. They remain a protected-main cleanup concern and must be rechecked by the
main auditor's final residual-process gate.

## 9. Findings and priorities

| ID | Priority | Finding / risk | Gate affected | Recommended action |
| --- | --- | --- | --- | --- |
| A8-P0-01 | P0 | v49 still exposes an active Qwen assistant and begins remote model preparation on Assistant open | frontend promotion, deterministic-runtime freeze | in a separately authorized frontend cleanup, remove/split the 10 runtime paths and regenerate the package lock; retain deterministic Search |
| A8-P0-02 | P0 | protected-main archive evidence says AI was retired, but it is untracked and four comparable files differ; there is no clean authoritative retirement commit usable by v49 | cleanup provenance, promotion | implement retirement from the measured v49 baseline; use `Archive/AI` only as recovery evidence, never as wholesale source |
| A8-P1-01 | P1 | the three executable probes can acquire/load model assets when invoked manually | repository hygiene, CI safety | move/freeze under a non-runtime research archive and exclude them from package/CI discovery |
| A8-P1-02 | P1 | four probe outputs describe 1,417 surfaces and machine-local paths, not frozen v48 | data/research quality | label historical; prohibit use as migration, release, rights, or corpus evidence |
| A8-P1-03 | P1 | package lock retains HF plus Node/Web ONNX runtimes, increasing install/build surface | frontend CI and supply chain | remove only after import removal; run focused dependency/license checks in the cleanup task |
| A8-P1-04 | P1 | dirty nested RAG lab has 9 modified reports and 6.9 GiB generated dependencies | protected-main hygiene, research reproducibility | obtain owner decision, freeze or discard modifications, then remove regenerable dependencies in a separate protected-main cleanup |
| A8-P1-05 | P1 | no CI/runtime policy in the audited v49 tree prevents reintroduction of hosted AI SDKs, model weights, or remote-model imports | repository hygiene | add a later data/frontend CI policy check after the runtime boundary is approved; A10 owns CI design |
| A8-P1-06 | P1 | 3 sleeping orphaned Node processes remain under protected main | machine hygiene | identify ownership outside this audit; terminate only with explicit authority |
| A8-P2-01 | P2 | AI prompt/report/system documents lack one uniform retired/non-authoritative banner | documentation clarity | add status metadata without deleting research history |

The two P0s are **delivery/runtime P0s**. A8 found no new archive-object
identity, TRACE cardinality, or PostgreSQL physical-schema fact. Physical DDL
can be evaluated independently by A4/A5/A6, but no frontend promotion or final
freeze may claim a deterministic runtime while A8-P0-01 remains open.

## 10. Acceptance and handoff

| A8 acceptance item | Status | Evidence |
| --- | --- | --- |
| SDK/model dependency inventory | PASS | one active HF dependency; no hosted generation SDK |
| Runtime import chain | PASS (audit), FAIL (retirement) | complete Reader-to-Qwen chain measured |
| Embedding/vector/RAG implementation classification | PASS | deterministic retrieval exists; vector/embedding implementation absent |
| Model weights and cache inventory | PASS | no v49 weights/cache; protected nested generated dependencies recorded |
| Prompt/report/history classification | PASS | all 42 tracked documentation paths assigned |
| Protected-main AI units | PASS (audit), PARTIAL (readiness) | 16 units classified; one dirty repo remains HOLD_UNKNOWN |
| Environment/secret non-disclosure | PASS | filenames only; no values or arguments emitted |
| Process inventory | PASS (A8 snapshot) | no task-owned process; pre-existing residuals separated |
| Retirement execution | NOT PERFORMED | prohibited by task scope |

### Explicitly not performed

- no model import, inference, tokenizer load, embedding, retrieval benchmark, or
  model download;
- no Node/Python/Flask service, Next server, build, TypeScript compiler,
  PostgreSQL, Docker, browser, Puppeteer, or Playwright run;
- no package install, dependency removal, lockfile rewrite, frontend edit,
  vector-index build, prompt execution, data export, or generated-output update;
- no secret value, environment block, model token, or process argument read or
  printed;
- no protected-main, nested-repo, v48 data, QA screenshot, manifest, shard, or
  frozen receipt modification;
- no process termination, cleanup, deletion, commit, push, merge, PR, or deploy.

### Readiness conclusion

- `AI_RAG_SLM_AUDIT_COVERAGE=COMPLETE`
- `AI_RUNTIME_RETIRED=false`
- `AI_RESEARCH_ARCHIVE_CLASSIFIED=true`
- `AI_UNKNOWN_OWNER_DECISIONS=1`
- `AI_TASK_RESIDUAL_PROCESSES=0`
- `AI_FRONTEND_PROMOTION_READY=false`

Next work must use this report and A7/A10 as the acceptance boundary for a
separate deterministic-runtime cleanup. It must not be folded into physical
DDL or inferred from the protected dirty main.
