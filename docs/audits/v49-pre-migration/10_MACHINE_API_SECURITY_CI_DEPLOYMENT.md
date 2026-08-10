# A10 — Machine API、Security、CI 与 Deployment 审计

- 审计包：**A10**
- 日期：2026-08-11（Australia/Brisbane）
- Worktree：`/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch / baseline：`refactor/v49-data-platform` @ `f076ca3444aaa0f413bb61fe2cb568d6a9aa2720`
- 唯一输出：`docs/audits/v49-pre-migration/10_MACHINE_API_SECURITY_CI_DEPLOYMENT.md`
- 静态扫描覆盖：**COMPLETE**（见下列显式边界）
- 发布就绪度：**FAIL**

`COMPLETE` 仅表示本报告约定的本地静态路径、配置和规范已经有证据命令与结论；它不表示 API、CI、安全或部署已经实现。历史任意内容中的 secret 值扫描和依赖许可证法律审查分别保持 `PARTIAL`，没有被包装成“未发现即安全”。

## 1. Scope

本包审计以下边界：

- stable object / relation / claim URI；
- server-rendered、crawlable HTML、canonical URL、robots 和 sitemap；
- JSON-LD alternate、Linked Art、PROV-O、DCAT、JSON Schema；
- immutable release descriptor、release diff/change feed、machine-readable manifest；
- `/api/v1` 的 GET-only/read-only 约束、method surface、错误和缓存身份；
- rights-held pixel/service URL non-disclosure；
- `researchReleaseId + researchManifestSha256` 与 `visualRegistryVersion + registrySha256` 双版本绑定；
- `.env*`、credential/secret path、环境变量名、历史敏感文件路径；
- package scripts、runtime write path、source map/debug surface、security headers；
- GitHub Actions、data/frontend/promotion CI 的实际隔离；
- root/source/data/frontend/third-party license boundary；
- Vercel/其它 deployment config 与 production readiness。

检查路径包括：

- `ARCHITECTURE.md`、`DATA_MODEL_V49.md`、`READ_API_V1.md`、`MIGRATION_V48_TO_V49.md`、`ACCEPTANCE_GATES.md`；
- `docs/adr/**`、`docs/architecture/**`、相关 research/methodology 文档；
- `frontend/src/app/**`、`frontend/src/lib/**`、相关 components/types；
- `frontend/package.json`、`frontend/package-lock.json`、`frontend/next.config.ts`、`frontend/tsconfig.json`；
- `.gitignore`、`LICENSE`、`FRONTEND_DESIGN_LICENSE.md`、`README.md`；
- current tree 与 Git history 中仅按敏感**路径模式**选择的条目；
- A1、A3、A4、A6、A7 已固化的共享证据。

本包没有复查第三方网络条款、运行应用、探测 URL、执行 dependency scanner，或读取任何 secret 值。

## 2. Evidence commands

以下命令均为静态只读检查；唯一写操作是用 `apply_patch` 创建本报告。为防止 secret 泄漏，环境检查只输出路径和变量名，关键词检查只输出命中文件路径。

```sh
repo=/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform

git -C "$repo" branch --show-current
git -C "$repo" rev-parse HEAD
git -C "$repo" status --short

find "$repo/frontend/src/app/api" -type f -name route.ts -print
find "$repo/frontend/src/app" -type f \
  \( -name 'sitemap.*' -o -name 'robots.*' \) -print
find "$repo" -type f \
  \( -name '*.schema.json' -o -iname '*openapi*' -o -iname '*jsonld*' \
     -o -iname '*dcat*' -o -iname '*change*feed*' -o -iname '*release*diff*' \) \
  -not -path '*/node_modules/*' -not -path '*/.next/*' -print

rg -n 'generateMetadata|metadataBase|alternates|canonical|application/ld\+json|JSON-LD' \
  frontend/src docs ARCHITECTURE.md DATA_MODEL_V49.md READ_API_V1.md
rg -n -i 'Linked Art|PROV-O|DCAT|JSON Schema|change feed|release diff|stable URI' \
  ARCHITECTURE.md DATA_MODEL_V49.md READ_API_V1.md docs

sed -n '1,260p' READ_API_V1.md
sed -n '1,240p' docs/adr/0003-runtime-repository-and-fixture-mode.md
sed -n '1,280p' frontend/src/app/api/archive-assistant-evidence/route.ts
sed -n '1,220p' frontend/src/app/layout.tsx
sed -n '1,220p' 'frontend/src/app/surfaces/[id]/page.tsx'

find "$repo" -path '*/.git' -prune -o -path '*/node_modules' -prune \
  -o -path '*/.next' -prune -o -type f -name '.env*' -print
rg -o --no-filename 'process\.env\.[A-Za-z_][A-Za-z0-9_]*' "$repo" \
  --glob '!frontend/package-lock.json' --glob '!frontend/node_modules/**' \
  | sed 's/^process\.env\.//' | sort -u
git -C "$repo" ls-files | \
  rg -i '(^|/)(\.env|.*(secret|credential|token|private.?key|\.pem$|\.p12$|\.pfx$|id_rsa))'
git -C "$repo" log --all --format='COMMIT %H' --name-only -- \
  ':(glob)**/.env*' ':(glob)**/*.pem' ':(glob)**/*.p12' \
  ':(glob)**/*.pfx' ':(glob)**/id_rsa*'

jq '{scripts,dependencies,devDependencies}' frontend/package.json
jq -r '.packages|to_entries[]|select(.key!="")|.value.license // "MISSING"' \
  frontend/package-lock.json | sort | uniq -c

find . -type f \
  \( -name '*.map' -o -name 'vercel.json' -o -name 'netlify.toml' \
     -o -name 'Dockerfile*' -o -path '*/.github/workflows/*' \) \
  -not -path './.git/*' -not -path './frontend/node_modules/*' \
  -not -path './frontend/.next/*' -print
rg -l 'writeFile|appendFile|createWriteStream|mkdirSync|rmSync|unlinkSync' \
  frontend/src --glob '*.{ts,tsx}'
rg -l 'localStorage|sessionStorage|indexedDB' frontend/src --glob '*.{ts,tsx}'
rg -n 'console\.(log|debug|info|warn|error)\(' \
  frontend/src frontend/scripts --glob '*.{ts,tsx,js,mjs}'
```

共享证据复用，而没有重复其磁盘密集扫描：

- [01_GIT_WORKTREE_AND_HISTORY.md](01_GIT_WORKTREE_AND_HISTORY.md)
- [03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md](03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md)
- [04_DATABASE_AND_DDL_READINESS.md](04_DATABASE_AND_DDL_READINESS.md)
- [06_RIGHTS_AND_VISUAL_FEDERATION.md](06_RIGHTS_AND_VISUAL_FEDERATION.md)
- [07_FRONTEND_A4_AND_BUILD_COUPLING.md](07_FRONTEND_A4_AND_BUILD_COUPLING.md)

## 3. Measured repository surface

### 3.1 Machine/API artifacts

| Measurement | Result |
| --- | ---: |
| App Router page files | 26 |
| Page files with metadata/generateMetadata marker | 25 |
| Metadata definitions with canonical alternate | 0 |
| API route files | 1 |
| `/api/v1` route files | 0 |
| Current API methods | one `POST` |
| `sitemap.*` files | 0 |
| `robots.*` files | 0 |
| JSON-LD code paths | 0 |
| OpenAPI files | 0 |
| API/release DTO JSON Schema files | 0 |
| Other JSON Schema files | 1 (`db/manual_source_record.schema.json`) |
| Release diff/change-feed implementations | 0 |
| Checked-in source maps outside ignored build trees | 0 |
| Deployment configs | 0 |
| GitHub Actions/workflow files | 0 |

`db/manual_source_record.schema.json` is a legacy/manual ingest schema. It does not validate `/api/v1` envelopes, release manifests, objects, relations, claims, visual registry rows, cursors, errors, or change feeds.

### 3.2 Runtime and debug surface

| Measurement | Result | Interpretation |
| --- | ---: | --- |
| `frontend/package.json` scripts | 17 | operational surface, not CI |
| scripts matching Next start/build/dev or capture/verify patterns | 14 | must not be mistaken for independent receipts |
| server-side filesystem-write files under `frontend/src` | 0 | current application source has no detected local DB/file mutation path |
| browser-storage files | 2 | assistant timing/memory state only; still requires privacy disclosure |
| `console.*` call sites | 23 in 13 files | mainly audit/capture scripts plus assistant timing; release logging policy is absent |
| explicit `process.env.NAME` references | 0 | no documented runtime configuration contract exists either |

No detected server filesystem write does not make the one `POST` route a v49 read API. That route accepts a question, parses JSON and runs legacy in-process retrieval against the monolithic frontend data graph.

### 3.3 Secret-safe path results

| Check | Measured result | Assurance boundary |
| --- | --- | --- |
| current `.env*` files outside ignored build/dependency trees | 0 |
| tracked sensitive-name paths (`.env`, secret, credential, token, PEM/P12/PFX/private-key patterns) | 0 |
| exact `process.env.NAME` references | 0 variables |
| history paths matching `.env*`, PEM/P12/PFX and `id_rsa*` | 0 entries |
| arbitrary-content historical secret scan | not performed | **PARTIAL**; path absence cannot prove content absence |

No file content was printed by these checks. An eventual public/promotion gate still needs a purpose-built redacted scanner over current and reachable history, with findings recorded as commit/path/rule/variable only and any value encrypted or withheld.

### 3.4 Dependency and license metadata

`frontend/package-lock.json` is lockfile v3 and declares 217 non-root package entries. All 217 contain a `license` expression in lock metadata; this is metadata coverage, not license compliance.

| License expression | Entries |
| --- | ---: |
| MIT | 140 |
| Apache-2.0 | 25 |
| ISC | 19 |
| BSD-3-Clause | 16 |
| LGPL-3.0-or-later | 10 |
| Apache-2.0 AND LGPL-3.0-or-later | 3 |
| Apache-2.0 AND LGPL-3.0-or-later AND MIT | 1 |
| CC-BY-4.0 | 1 |
| 0BSD | 1 |
| MIT OR CC0-1.0 | 1 |

The 14 libvips/sharp platform entries containing LGPL terms and one CC-BY metadata entry require packaging/attribution/source-offer review appropriate to the actual distributed artifacts. This report makes no legal compatibility conclusion. The repository has no generated `NOTICE`, `THIRD_PARTY_LICENSES`, SBOM, license-policy receipt, or artifact-specific attribution bundle.

The root `LICENSE` is MIT, while `FRONTEND_DESIGN_LICENSE.md`, README exclusions, third-party provider data, reports and QA/media have separate boundaries. Root MIT must not be projected onto data, screenshots, provider metadata/images, reports, fonts or the visual design.

## 4. Machine-readable contract readiness

The following matrix separates design prose from executable delivery. `Implementation` means a local file/route/schema/testable artifact exists; no runtime command was used.

| # | Capability | Normative/design status | Current implementation | Evidence and decision |
| ---: | --- | --- | --- | --- |
| 1 | Exact immutable research identity | **PARTIAL** | absent | Generic `releaseId + manifestSha256` exists, but is not named/cross-pinned as the research half of a dual release. |
| 2 | Independent visual-registry identity | **FAIL** | absent | No `visualRegistryVersion + registrySha256`, manifest lifecycle or current CAS. |
| 3 | Stable object URI | **PARTIAL** | partial prototype | `/surfaces/{surfaceId}` exists, but no normative absolute URI template, host/version/canonical policy or archive-object URI. |
| 4 | Stable relation URI | **FAIL** | absent | TRACE type page is taxonomy navigation, not a stable semantic-relation resource URI. |
| 5 | Stable claim URI | **FAIL** | absent | No claim endpoint/URI/template; relation, claim and TRACE projection still require pre-DDL separation per A4/A5. |
| 6 | SSR crawlable object HTML | **PARTIAL** | source-level partial | Surface is a force-dynamic server page, but crawlability, release pinning and canonical identity are unverified; no browser was run. |
| 7 | Canonical URL/alternate | **FAIL** | absent | 25 metadata definitions, zero canonical alternates and no `metadataBase`. |
| 8 | JSON-LD alternate | **FAIL** | absent | No code route or JSON-LD block. |
| 9 | Linked Art mapping | **FAIL** | absent | Mentioned only as future research interoperability, without term-to-field mapping or conformance fixture. |
| 10 | PROV-O mapping | **FAIL** | absent | Provenance model exists conceptually, but no RDF mapping/context/shape. |
| 11 | DCAT release catalog/manifest | **FAIL** | absent | No DCAT dataset/distribution/checksum mapping. |
| 12 | API/release JSON Schema | **FAIL** | absent | The sole schema is unrelated legacy manual-record input. |
| 13 | Release diff | **FAIL** | absent | No stable diff resource, units, tombstones or compatibility rule. |
| 14 | Change feed | **FAIL** | absent | No release-sequenced feed, cursor or retention contract. |
| 15 | Sitemap/robots | **FAIL** | absent | Neither App Router metadata route exists. |
| 16 | GET/HEAD/OPTIONS-only `/api/v1` | **PASS (design only)** | absent | `READ_API_V1.md` is explicit; current only route is POST outside `/api/v1`. |
| 17 | Pixel/service URL fail-closed response | **PARTIAL prose / FAIL enforceability** | absent | DTO prose says rights-safe, but no schema/projector/negative test; current HTML directly renders `image.url` for IMG01/02/03. |
| 18 | Dual-version cursor/cache/ETag/log binding | **FAIL** | absent | Generic release hash caching is described; research+visual exact-pair compatibility is missing. |

Quantified result:

- design/normative layer: **1 PASS / 4 PARTIAL / 13 FAIL**;
- executable machine-contract implementation: **0 / 18 complete**;
- machine-readable freeze readiness: **false**;
- deployment/promotion readiness: **false**.

The useful `READ_API_V1.md` baseline should be retained, but it is not evidence that an endpoint, schema, RDF mapping, crawler contract or non-disclosure test exists.

## 5. Current API and HTML observations

### 5.1 Existing route is not `/api/v1`

`frontend/src/app/api/archive-assistant-evidence/route.ts` exports only `POST`. It:

- accepts JSON with `question`, optional research flag and limited context;
- rejects empty or over-2,000-character questions;
- performs in-process legacy retrieval;
- returns evidence candidates including `surfaceId`, descriptive fields, `imageState` and `sourceUrl`;
- does not return `image.url` in the candidate DTO.

Static gaps include no explicit authentication, rate limit, request content-type policy, cache policy, CORS policy, stable response schema, release/manifest identity, visual-registry identity, security logging contract or abuse receipt. Because retrieval scans legacy archive data, a bounded request body alone does not bound server work. A8 owns retirement of the surrounding local-model/RAG experiment; this audit only records the HTTP/security boundary.

### 5.2 Current HTML can emit remote pixel locators

`SurfaceImage` carries `url`. `ImageZone.tsx`, main/sub-sheet, card and text-page renderers send that URL to `<img>` for legacy IMG01/02/03 states. `referrerPolicy="no-referrer"` reduces one disclosure channel but is not authorization, policy evaluation, endpoint health, takedown enforcement or registry pinning.

The future API prose says unrestricted/rights-held URLs are excluded, but there is no executable projection or schema to prove that rule. A6 establishes the pre-DDL requirement:

```text
unknown | missing | conflict | stale
  -> LINK_ONLY or CITATION_ONLY
  -> no thumbnail, image-service, direct-pixel or proxy URL
```

API success, HTTP redirect, IIIF availability or endpoint health may never upgrade rights assessment or delivery mode.

### 5.3 Crawlability is source-level only

The repository has server page modules and stable-looking relative paths, which is better than a client-only SPA. It does not yet establish a machine publication contract:

- no absolute canonical URI namespace;
- no canonical link alternate;
- no sitemap or robots policy;
- no release-pinned HTML identity;
- no object/relation/claim JSON-LD alternate;
- no HTTP/browser verification;
- TRACE and Reader components remain heavily client-oriented and consume fixed v48 assets.

Therefore `SSR crawlable HTML` is `PARTIAL`, not `PASS`.

## 6. CI separation and delivery readiness

### 6.1 Architecture versus implementation

The nine v49 documents correctly describe three independent lanes:

1. data CI owns schema/import/lineage/rights/research/reconciliation/release receipts and never runs Next;
2. frontend CI consumes a pinned fixture or sealed release and never connects to canonical PostgreSQL or generates data;
3. promotion consumes both immutable receipts and alone may run full production build/browser validation.

Measured implementation:

| Lane/capability | Workflow files | Independent cache/artifact boundary | Machine receipt | Status |
| --- | ---: | --- | --- | --- |
| Data CI | 0 | absent | absent | **FAIL implementation** |
| Frontend CI | 0 | absent | absent | **FAIL implementation** |
| Promotion orchestration | 0 | absent | absent | **FAIL implementation** |
| Secret/history scan | 0 | absent | absent | **FAIL implementation** |
| Dependency/license scan | 0 | absent | absent | **FAIL implementation** |

Package scripts are developer entry points, not independent CI. There is no `.github/workflows`, no other detected CI config, and no immutable receipt exchange. G8 is therefore architecture `PASS/PARTIAL` as already defined, implementation `FAIL/not present`; it cannot support freeze or promotion.

### 6.2 Deployment configuration

No `vercel.json`, Dockerfile/compose, Procfile, Netlify/Render/Fly config or equivalent deployment manifest was found. `next.config.ts` contains static-generation throttles and production webpack cache suppression, but no security headers, CSP, API rate policy, release/visual-registry configuration, observability drain, health endpoint, immutable asset publication or rollback automation.

There are zero explicit environment-variable consumers, which also means there is no declared fail-closed production mode selector or secret/config contract in current code. Deployment readiness is **false**; absence of configuration is not a “secure default” receipt.

### 6.3 Runtime writes and client state

No server filesystem-write primitive was detected under `frontend/src`. Two browser files use local/session storage for assistant memory/timing. These values are not canonical writes, but production requires a privacy/retention statement and must ensure query/history text is not logged or promoted into telemetry without consent.

## 7. Cross-audit consistency

| Evidence package | Reused conclusion | A10 consequence |
| --- | --- | --- |
| A1 Git/history | 78 reachable blobs ≥100 MiB; no SBOM/third-party license ledger; A1 history-secret path command was inconclusive | public-repo security/license and repository hygiene remain promotion blockers; A10 supplied a narrow path-only history check but not content assurance |
| A3 data/lineage | JSON is sole migration input; Search/TRACE are derived; 1,266 tracked raw provider files lack comprehensive redaction-review receipt | no raw/provider payload may flow to machine API merely because tracked; artifact disposition is required |
| A4 DDL | dual release/visual identity, claim/relation separation, role/default privileges and machine-readable gates are P0 | stable URI and dual-version contracts must be fixed before physical DDL, not retrofitted after API implementation |
| A6 rights | visual registry/CAS, endpoint roles, rights/delivery/health axes and takedown are absent | current remote URLs cannot be certified rights-safe; machine responses need exact dual identity and fail-closed projection |
| A7 frontend/build | 26 direct runtime/compile consumers plus 9 producers; data change still requires frontend delivery; current runtime mixes 8,636 and 15,923 populations | API/repository and deployment receipts must replace fixed asset discovery; no current page is release/registry pinned |

No cross-report conflict was found in these conclusions. A10 does not duplicate A6's rights inventory or A7's A4/build count.

## 8. Findings and priorities

### P0

| ID | Finding / affected paths | Risk | Recommended action | Gate |
| --- | --- | --- | --- | --- |
| A10-P0-01 | Stable archive-object, semantic-relation and claim URI templates are absent; `READ_API_V1.md`, `DATA_MODEL_V49.md` | identifiers can become route-specific or projection-specific; claims cannot be cited independently | Before DDL, define absolute URI namespace, immutable ID mapping, alias/withdraw/split behavior, and separate object/relation/claim/TRACE resources | PRE_DDL |
| A10-P0-02 | Research release and visual registry are not independent exact pairs in envelopes, cursors, ETags, caches or logs; all nine normative docs | rights/health/takedown updates can rewrite research identity or clients can mix incompatible versions | Adopt A6 dual-version contract, cross-pin compatibility and separate CAS pointers; every visual-bearing response carries both exact pairs | PRE_DDL |
| A10-P0-03 | Machine-readable publication contract is absent: API/release JSON Schema, JSON-LD, Linked Art/PROV-O, DCAT and non-disclosure shapes | prose-only DTOs drift; external users cannot validate releases; rights-held fields can leak | Define versioned JSON Schemas and normative mappings; validate negative rights cases and stable IDs before freeze | PRE_DDL semantics / FREEZE |
| A10-P0-04 | Rights-safe API cannot be enforced; current HTML renderers directly use legacy `image.url`; future contract has no projection/schema tests | unknown/stale/conflict rights or healthy endpoint can expose a pixel | Seal a visual registry; suppress pixel/service fields for fail-closed states; test API/IIIF/redirect/health never grant delivery; takedown always wins | PRE_DDL rights / PROMOTION |
| A10-P0-05 | Zero CI workflows and zero independent receipts despite documented data/frontend split | migration or data changes can silently alter frontend output; no promotion proof | Implement independent data/frontend CI after contracts exist, with immutable receipt handoff and promotion-only full build/browser lane | FREEZE/PROMOTION, not DDL creation |
| A10-P0-06 | 1,266 raw-provider files and third-party artifacts lack comprehensive redaction/rights/license disposition; root MIT is insufficient | secret/provider-policy/license material could enter public Git artifacts or API | artifact-level owner/terms/redaction/rights/license ledger; HOLD_UNKNOWN remains non-public and non-ingestable | RAW INGEST/FREEZE/PROMOTION |
| A10-P0-07 | No production deployment security contract/config: no fail-closed mode, CSP/headers, rate limiting, health, rollback or dual-version env/config validation | prototype behavior can be deployed accidentally with POST assistant and fixed v48 assets | Write a later deployment threat model/config only after data/API/frontend receipts pass; default startup must reject fixture/unpinned releases | PROMOTION/DEPLOYMENT |

### P1

| ID | Finding / affected paths | Risk | Recommended action |
| --- | --- | --- | --- |
| A10-P1-01 | No canonical alternates, sitemap or robots route; 25 metadata definitions are title/description only | duplicate/non-crawlable resources and unstable citation | add release-aware canonical policy and generated sitemap after URI contract; exclude held/review-only resources |
| A10-P1-02 | No release diff/change feed | consumers cannot discover merge/split/withdraw/takedown or invalidate derived indexes safely | define release-to-release change units, tombstones, compatibility and cursor retention |
| A10-P1-03 | Existing assistant POST has no rate-limit/auth/cache/schema/release binding | compute abuse, ambiguous data identity and unstable integration | retire/quarantine per A8, or isolate outside `/api/v1` with explicit policy until removed |
| A10-P1-04 | No `NOTICE`, `THIRD_PARTY_LICENSES`, SBOM or license-policy receipt; 15 lock entries have LGPL/CC-BY-bearing expressions | distribution obligations can be missed | generate reviewed SBOM/notices from exact release artifact; do not infer compliance from lock metadata |
| A10-P1-05 | Historical secret assurance is path-only; no redacted content scanner receipt | embedded keys in ordinary filenames/history remain possible | run approved current+reachable-history scanner with value redaction and revocation workflow before public promotion |
| A10-P1-06 | 23 console calls and browser assistant storage have no telemetry/privacy contract | query/context data or debug timing can leak | allowlisted structured logs carrying dual release IDs; redact payloads; document browser retention and consent |
| A10-P1-07 | No security/dependency automation or update policy | vulnerable packages and license changes can pass unnoticed | add pinned audit/SBOM/license/security jobs to frontend CI; results are independent from data acceptance |

### P2

| ID | Finding / affected paths | Risk | Recommended action |
| --- | --- | --- | --- |
| A10-P2-01 | No checked-in source maps found, but there is no explicit release source-map/debug policy | a future platform default can publish them | define artifact allowlist and verify deployment output; do not rely on current absence |
| A10-P2-02 | No OpenAPI contract | client generation and method/security review remain manual | generate OpenAPI from the same JSON Schemas without making it a second authority |
| A10-P2-03 | API accessibility/localization semantics for machine-readable attribution are unspecified | required statements may be reordered or inaccessible | define ordered language-tagged attribution arrays and HTML/JSON conformance tests |

Priority totals contributed by A10: **P0 7 / P1 7 / P2 3**.

## 9. Required gate outcomes

| Gate | A10 result | Reason |
| --- | --- | --- |
| Stable object/relation/claim identity | **FAIL** | object route partial; relation/claim URI contracts absent |
| Crawlable SSR + canonical | **PARTIAL** | server page modules exist; canonical/sitemap/robots/release pin absent |
| JSON-LD / Linked Art / PROV-O | **FAIL** | aspirational prose only |
| DCAT + release manifest mapping | **FAIL** | absent |
| JSON Schema / machine validation | **FAIL** | no API/release/visual schemas |
| Release diff/change feed | **FAIL** | absent |
| GET-only API design | **PASS (document only)** | explicit in `READ_API_V1.md`; no implementation |
| GET-only API implementation | **FAIL** | zero `/api/v1` routes; existing route is POST |
| Rights-held pixel URL non-disclosure | **FAIL** | no enforceable dual-version projection; current HTML uses remote URLs |
| Research/visual dual version | **FAIL** | visual registry identity/CAS absent |
| Secret current-path hygiene | **PASS with bounded evidence** | no `.env`/key-like path or env variable reference found |
| Secret reachable-history content assurance | **PARTIAL** | sensitive paths checked; arbitrary content not scanned |
| Dependency license metadata | **PASS** | all 217 lock entries declare expressions |
| Dependency/license compliance | **PARTIAL** | no legal/artifact review, notice or SBOM |
| Data/frontend CI separation design | **PASS/PARTIAL** | clear normative design, but acceptance itself says workflows pending |
| Data/frontend CI separation implementation | **FAIL** | zero workflows/receipts |
| Deployment readiness | **FAIL** | no production config/security/rollback/receipt |

Readiness booleans for this package:

```text
MACHINE_CONTRACT_PRE_DDL_READY=false
RIGHTS_SAFE_MACHINE_DELIVERY_READY=false
CI_IMPLEMENTED=false
SECURITY_FREEZE_READY=false
DEPLOYMENT_READY=false
FRONTEND_PROMOTION_READY=false
```

## 10. Recommended action order

1. **Close pre-DDL identity and visual federation semantics.** Acceptance: stable object/relation/claim URI templates; semantic claim distinct from TRACE projection; exact research and visual pairs; endpoint roles; orthogonal rights/delivery/health; fail-closed/takedown behavior; all normative docs use one vocabulary.
2. **Create machine contract artifacts after semantic closure.** Acceptance: API/release/visual JSON Schemas, JSON-LD contexts and Linked Art/PROV-O/DCAT mappings; GET-only resource list; canonical/sitemap policy; diff/change feed; negative schemas/tests prove no held pixel URL.
3. **Implement independent CI and deployment only after data/API adapters exist.** Acceptance: independent data/frontend receipts, promotion consumes exact pair, redacted secret scan, SBOM/license receipt, headers/rate/health/rollback, and deployment refuses fixture or unpinned identity.

## 11. Actions explicitly not performed

- No network access, remote API/IIIF/image request, download or provider probe.
- No `.env`, credential, key or token value was opened, printed or copied.
- No exhaustive historical content secret scanner, vulnerability scanner, license checker or legal determination.
- No npm install, Next dev/build/start, TypeScript, lint, browser, screenshot or frontend render.
- No PostgreSQL, SQLite query, Docker, migration, data export/regeneration or sidecar creation.
- No package, lockfile, frontend, CI, deployment, v48 data, shard, manifest, QA screenshot or dirty-main modification.
- No cleanup, delete, checkout, reset, clean, merge, rebase, commit, push, PR or deploy.
- No current `POST` endpoint was called; no security finding was exploit-tested.
- No statement treats API availability, IIIF, redirects, endpoint health, Git presence or root MIT as rights authorization.

## 12. Residual processes and completion receipt

- A10 started no Node, Next, TypeScript, PostgreSQL, Docker, browser automation, data generator, package installer, server or background process.
- All A10 shell commands completed; no A10 execution session remains.
- A10 did not perform the OS-wide final process scan; the main auditor owns the final authorized residual-process gate.
- This report is the only A10-authored path.

## 13. Final A10 decision

The static audit is complete enough to support a traced decision: the repository has a useful read-only API design baseline and server-route prototype, but not a machine-readable publication system. Stable relation/claim identity, dual research/visual versioning and enforceable rights-safe delivery are pre-DDL P0 gaps. API schemas/mappings, independent CI, repository-wide secret/license receipts and deployment controls are freeze/promotion P0 gaps.

**A10 audit coverage: COMPLETE. A10 readiness: FAIL. PRE_DDL_READY contribution: false.**
