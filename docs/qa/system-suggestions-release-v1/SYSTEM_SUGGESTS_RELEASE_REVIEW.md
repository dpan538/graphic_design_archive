# System Suggests — release-readiness review (2026-09-06)

Scope: the four active surfaces (SEARCH_RESULTS, TRACE_CONTEXT, TRACE_VALIDATED_EXPLORATION, TRACE_OPEN_INQUIRY); TRACE_SPACETIME stays deferred (404 before any provider). Request schema v2: the page names its state (query + filters; object + on-canvas ids; map + state; inquiry id) and may state what it shows; the server resolves the facts from the authoritative reader (`facts.server.ts`), checks the shown counts, and only then builds candidates, a cache key and a prompt. A v1 TRACE context that describes its own facts is answered deterministically and never reaches a model.

**Model and system.** The model composes one or two sentences (≤ 45 words) from FACT STATEMENTS and returns `note`, `used_fact_ids`, `suggestion_ids`; the gate (`assertFactualNote`) re-reads the note against the facts: every number a supplied count, every quoted term a supplied label, a sentence that pairs names exactly one shown pair (a chain never becomes a star, A—B and B—C never A—C), no source or record counts, no weak / strong / similar / semantic / co-occurring, no promise of results, no missing / absent / never existed for set-aside or not-recorded context, no likely / possible framing of an inquiry, no cause, influence, sequence, history. Anything else falls back to the deterministic note from the same facts — never a trimmed model sentence.

**Provider.** DeepSeek Responses: only assistant message `output_text` parts are read; reasoning items are skipped; error, incomplete and empty responses fail closed (PROVIDER_ERROR / PROVIDER_INCOMPLETE / PROVIDER_OUTPUT_MISSING); 429 is PROVIDER_RATE_LIMITED; malformed JSON is PROVIDER_OUTPUT_INVALID. Configuration: `deepseek-v4-flash`, `reasoning.effort: none`, temperature 0 (env `SYSTEM_SUGGESTIONS_TEMPERATURE` for the 0.2 comparison), `max_output_tokens 512`, no tools, no streaming, strict JSON schema, `store: false`, timeout 2.5 s (cap 5 s). Zero suggestions is a legal answer on every surface; the ceilings are Search 2 · Context 1 · Exploration 0 · Inquiry 1.

**Cache.** Key = surface · release/data version · context fingerprint · prompt version · language · model configuration; bounded (500), expiring (Search 5 min, governed surfaces 30 min), in-flight requests for one key merged, a last-good copy (6 h) served when the provider fails for the same facts. The fingerprint covers the visible association set, so the same four words with other edges are another key; a template change is not.

## Matrix

| Group | Passed | Failed cases |
| --- | --- | --- |
| Search | 9/9 | — |
| Context Canvas | 8/8 | — |
| Validated Exploration | 10/10 | — |
| Open Inquiry | 15/15 | — |
| Input and safety | 10/10 | — |
| Provider | 12/12 | — |
| Cache and race | 5/5 | — |
| Product boundary | 8/8 | — |
| Dev server | 9/9 | — |

**Result: PASS — 86/86 cases.** Mock providers prove the contract; they say nothing about the live service's availability. The live provider run is reported separately (`system-suggests-live-results.jsonl`, `npm run verify:system-suggestions-live-v1`).

## Three verdicts

| Item | Requirement | Verdict |
| --- | --- | --- |
| Facts and boundaries | relations, counts and scopes shown to the reader are correct; no unauthorised action or data exposure | PASS (mock and deterministic) |
| Real provider | effective output rate, fallback reasons, latency reported with sample size | see the live results file: SKIPPED when no key is present in the environment; never claimed from mock runs |
| Experience and isolation | short, readable, checkable notes; no stale note; core pages never blocked | PASS (service and HTTP); the page-level operations are in the report's browser section |

## Cases

| Id | Group | Case | Surface | Source | Status | Note | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SS-001 | Search | zero results | SEARCH_RESULTS | MODEL | MODEL_OK | No public objects match this Search for the text "zzqx-no-match". | PASS |
| SS-002 | Search | single result | SEARCH_RESULTS | MODEL | MODEL_OK | 1 public object matches this Search for the text "SURF-AICTRACEV47R0001". | PASS |
| SS-003 | Search | multi results | SEARCH_RESULTS | MODEL | MODEL_OK | 508 public objects match this Search for the text "poster". | PASS |
| SS-004 | Search | multiple filters | SEARCH_RESULTS | STATIC_FALLBACK | PROVIDER_DISABLED | 25 public objects match this Search for the text "poster", the object type Poster and the years 1960–1969. 24 of the 25  | PASS |
| SS-005 | Search | no refinement available | SEARCH_RESULTS | STATIC_FALLBACK | PROVIDER_DISABLED | 25 public objects match this Search for the text "poster", the object type Poster and the years 1960–1969. 24 of the 25  | PASS |
| SS-006 | Search | forward and back | SEARCH_RESULTS | — | — |  | PASS |
| SS-007 | Search | promise of more results | SEARCH_RESULTS | STATIC_FALLBACK | INVALID_RESPONSE | 508 public objects match this Search for the text "poster". 112 of the 508 matching objects are dated to the 1980s. | PASS |
| SS-008 | Search | absence claim | SEARCH_RESULTS | STATIC_FALLBACK | INVALID_RESPONSE | No public objects match this Search for the text "zzqx-no-match". | PASS |
| SS-009 | Search | shown count mismatch | SEARCH_RESULTS | — | — |  | PASS |
| SS-010 | Context Canvas | three dimensions, all on canvas | TRACE_CONTEXT | MODEL | MODEL_OK | The selected object is AIDS Crisis, a poster. Medium: Poster on the canvas. | PASS |
| SS-011 | Context Canvas | some set aside | TRACE_CONTEXT | MODEL | MODEL_OK | The selected object is AIDS Crisis, a poster. | PASS |
| SS-012 | Context Canvas | missing dimension | TRACE_CONTEXT | STATIC_FALLBACK | PROVIDER_DISABLED | The selected object is Portfolio Cover for Mexican People, a lithograph; book; prints and drawing; print. Medium: Portfo | PASS |
| SS-013 | Context Canvas | not recorded read as absence | TRACE_CONTEXT | STATIC_FALLBACK | INVALID_RESPONSE | The selected object is Portfolio Cover for Mexican People, a lithograph; book; prints and drawing; print. Medium: Portfo | PASS |
| SS-014 | Context Canvas | switch object | TRACE_CONTEXT | — | — |  | PASS |
| SS-015 | Context Canvas | invented on-canvas id | — | — | — |  | PASS |
| SS-016 | Context Canvas | invented relation between contexts | TRACE_CONTEXT | STATIC_FALLBACK | INVALID_RESPONSE | The selected object is AIDS Crisis, a poster. Medium: Poster on the canvas. | PASS |
| SS-017 | Context Canvas | no invented add action | TRACE_CONTEXT | — | — |  | PASS |
| SS-018 | Validated Exploration | single pair | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_DISABLED | In this view, trade is paired with design diplomacy. | PASS |
| SS-019 | Validated Exploration | three-term chain, one pair narrated | TRACE_VALIDATED_EXPLORATION | MODEL | MODEL_OK | In this view, trade is paired with propaganda. | PASS |
| SS-020 | Validated Exploration | chain written as a star | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | INVALID_RESPONSE | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-021 | Validated Exploration | A—B, B—C read as A—C | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | INVALID_RESPONSE | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-022 | Validated Exploration | four-term chain | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_DISABLED | Design diplomacy is shown here alongside trade, propaganda and exhibition through three evidence-qualified generic assoc | PASS |
| SS-023 | Validated Exploration | same terms, different edges | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_DISABLED | Design diplomacy is shown here alongside propaganda and trade through two evidence-qualified generic associations. | PASS |
| SS-024 | Validated Exploration | different starting point | TRACE_VALIDATED_EXPLORATION | — | — |  | PASS |
| SS-025 | Validated Exploration | association counted as sources | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | INVALID_RESPONSE | In this view, trade is paired with design diplomacy. | PASS |
| SS-026 | Validated Exploration | generic read as weak or semantic | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | INVALID_RESPONSE | In this view, trade is paired with design diplomacy. | PASS |
| SS-027 | Validated Exploration | association details entry | TRACE_VALIDATED_EXPLORATION | — | — |  | PASS |
| SS-028 | Open Inquiry | inquiry 7b7c9540 | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between commodification, mediation and mobile object. The current evidenc | PASS |
| SS-029 | Open Inquiry | inquiry 915b6f43 | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between canonization, exclusion and gendering. The current evidence does  | PASS |
| SS-030 | Open Inquiry | inquiry 966cf341 | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between exhibition and design diplomacy. The current evidence does not qu | PASS |
| SS-031 | Open Inquiry | inquiry ec1406fd | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between adaptation and cultural negotiation. The current evidence does no | PASS |
| SS-032 | Open Inquiry | inquiry 07071d2a | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between institutionalization, professional education or training NEW and  | PASS |
| SS-033 | Open Inquiry | inquiry 8e8f223b | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between adaptation, contact-zone negotiation NEW and rejection. The curre | PASS |
| SS-034 | Open Inquiry | inquiry 08be4a71 | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between exhibition, trade, propaganda and design diplomacy. The current e | PASS |
| SS-035 | Open Inquiry | inquiry 14fbd576 | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between institutionalization, design education and professionalization. T | PASS |
| SS-036 | Open Inquiry | inquiry e94f887c | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between craft and design education. The current evidence does not qualify | PASS |
| SS-037 | Open Inquiry | inquiry 6a2555c5 | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between exhibition, propaganda and design diplomacy. The current evidence | PASS |
| SS-038 | Open Inquiry | inquiry 461dcb47 | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | PROVIDER_DISABLED | This open inquiry considers a bounded question between consumption, production site, production, material displacement a | PASS |
| SS-039 | Open Inquiry | all public inquiries | — | — | — |  | PASS |
| SS-040 | Open Inquiry | same words as a generic pair, other scope | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | INVALID_RESPONSE | This open inquiry considers a bounded question between exhibition and design diplomacy. The current evidence does not qu | PASS |
| SS-041 | Open Inquiry | framed as likely | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | INVALID_RESPONSE | This open inquiry considers a bounded question between commodification, mediation and mobile object. The current evidenc | PASS |
| SS-042 | Open Inquiry | unknown inquiry | — | — | — |  | PASS |
| SS-043 | Input and safety | forged state | — | — | — |  | PASS |
| SS-044 | Input and safety | forged counts | — | — | — |  | PASS |
| SS-045 | Input and safety | cross-surface reference | — | — | — |  | PASS |
| SS-046 | Input and safety | client-described facts | — | STATIC_FALLBACK | LEGACY_CONTEXT_STATIC | Invented term is shown here alongside another through one evidence-qualified generic association. | PASS |
| SS-047 | Input and safety | instruction in the query | SEARCH_RESULTS | MODEL | MODEL_OK | No public objects match this Search for the entered text. | PASS |
| SS-048 | Input and safety | HTML in the query | SEARCH_RESULTS | STATIC_FALLBACK | PROVIDER_DISABLED | No public objects match this Search for the entered text. | PASS |
| SS-049 | Input and safety | URL in the query | SEARCH_RESULTS | STATIC_FALLBACK | PROVIDER_DISABLED | No public objects match this Search for the entered text. | PASS |
| SS-050 | Input and safety | model obeys the injection | SEARCH_RESULTS | STATIC_FALLBACK | INVALID_RESPONSE | No public objects match this Search for the entered text. | PASS |
| SS-051 | Input and safety | unknown request field | — | — | — |  | PASS |
| SS-052 | Input and safety | oversized body | — | — | — |  | PASS |
| SS-053 | Provider | normal message | TRACE_VALIDATED_EXPLORATION | MODEL | MODEL_OK | In this view, trade is paired with propaganda. | PASS |
| SS-054 | Provider | reasoning before the message | TRACE_VALIDATED_EXPLORATION | MODEL | MODEL_OK | In this view, trade is paired with propaganda. | PASS |
| SS-055 | Provider | reasoning only | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_OUTPUT_MISSING | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-056 | Provider | empty content | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_OUTPUT_MISSING | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-057 | Provider | bad JSON | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_OUTPUT_INVALID | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-058 | Provider | truncated | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_INCOMPLETE | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-059 | Provider | 429 | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_RATE_LIMITED | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-060 | Provider | 500 | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_ERROR | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-061 | Provider | error object | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | PROVIDER_ERROR | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-062 | Provider | timeout | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | TIMEOUT | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-063 | Provider | request configuration | TRACE_VALIDATED_EXPLORATION | — | — |  | PASS |
| SS-064 | Provider | prompt carries facts, not client context | TRACE_VALIDATED_EXPLORATION | — | — |  | PASS |
| SS-065 | Cache and race | same facts, other template | TRACE_VALIDATED_EXPLORATION | MODEL | MODEL_OK_CACHED | In this view, trade is paired with propaganda. | PASS |
| SS-066 | Cache and race | simultaneous requests merge | TRACE_VALIDATED_EXPLORATION | MODEL | MODEL_OK | In this view, exhibition is paired with propaganda. | PASS |
| SS-067 | Cache and race | one term richer → new facts | TRACE_VALIDATED_EXPLORATION | — | — |  | PASS |
| SS-068 | Cache and race | late answer keeps its own state | — | MODEL | MODEL_OK | In this view, trade is paired with propaganda. | PASS |
| SS-069 | Cache and race | Search cache is short and keyed by fingerprint | — | — | — |  | PASS |
| SS-070 | Product boundary | Spacetime not released | — | — | — |  | PASS |
| SS-071 | Product boundary | no provider: Search | SEARCH_RESULTS | STATIC_FALLBACK | NO_KEY | 508 public objects match this Search for the text "poster". 112 of the 508 matching objects are dated to the 1980s. | PASS |
| SS-072 | Product boundary | no provider: Context | TRACE_CONTEXT | STATIC_FALLBACK | NO_KEY | The selected object is AIDS Crisis, a poster. Medium: Poster set aside. | PASS |
| SS-073 | Product boundary | no provider: Exploration | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | NO_KEY | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-074 | Product boundary | no provider: Inquiry | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | NO_KEY | This open inquiry considers a bounded question between commodification, mediation and mobile object. The current evidenc | PASS |
| SS-075 | Product boundary | guidance off | — | STATIC_FALLBACK | PROVIDER_DISABLED | 508 public objects match this Search for the text "poster". 112 of the 508 matching objects are dated to the 1980s. | PASS |
| SS-076 | Product boundary | export independent of guidance | — | — | — |  | PASS |
| SS-077 | Product boundary | rate limiter scope | — | — | — |  | PASS |
| SS-078 | Dev server | server | — | — | — |  | PASS |
| SS-079 | Dev server | POST Search | SEARCH_RESULTS | STATIC_FALLBACK | NO_KEY | 508 public objects match this Search for the text "poster". 112 of the 508 matching objects are dated to the 1980s. | PASS |
| SS-080 | Dev server | POST Context | TRACE_CONTEXT | STATIC_FALLBACK | NO_KEY | The selected object is AIDS Crisis, a poster. Medium: Poster set aside. | PASS |
| SS-081 | Dev server | POST Exploration | TRACE_VALIDATED_EXPLORATION | STATIC_FALLBACK | NO_KEY | Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations. | PASS |
| SS-082 | Dev server | POST Inquiry | TRACE_OPEN_INQUIRY | STATIC_FALLBACK | NO_KEY | This open inquiry considers a bounded question between commodification, mediation and mobile object. The current evidenc | PASS |
| SS-083 | Dev server | POST Spacetime | — | — | — |  | PASS |
| SS-084 | Dev server | POST forged count | — | — | — |  | PASS |
| SS-085 | Dev server | Exploration page | — | — | — |  | PASS |
| SS-086 | Dev server | Search page | — | — | — |  | PASS |

## Browser operations (the in-app browser against the dev server, no provider key: every note is the deterministic one from the same facts)

| Case | Result | What was seen |
| --- | --- | --- |
| Search: live count and guidance | PASS | 508 results · note '508 public objects match this Search for the text "poster". 112 of the 508 matching objects are dated to the 1980s.' · buttons Focus on 1980s, Focus on Poster · 1 dialog |
| Search: refinement click | PASS | ?q=poster&yearFrom=1980&yearTo=1989 · 113 results (API 113) · note '113 public objects match … the years 1980–1989. 112 of the 113 matching objects are dated to the 1980s.' · 1 dialog, 1 System suggests |
| Search: paging | PASS | after=1 · Page 2 / 5 · 25 rows |
| Exploration: Description note from facts | PASS | note 'Design diplomacy is shown here alongside trade and propaganda through two evidence-qualified generic associations.' · pairs trade — propaganda, trade — design diplomacy · 0 buttons |
| Exploration: View association details | PASS | Association trade · propaganda · Basis: 'trade and propaganda are available together as an evidence-qualified generic association.' · Sources: not public |
| Open Inquiry: disclosure order and note | PASS | note 'This open inquiry considers a bounded question between commodification, mediation and mobile object. The current evidence does not qualify this question for the validated graph.' · action Return to exploration |
| Search window doubled by the modal route | PASS | found: router.replace on /search mounted the intercepting (.)search modal as a second window (2 dialogs, 2 System suggests); fixed by syncing the URL through history.replaceState; re-checked: 1 dialog |

The dev server on this machine holds no provider key, so every note above is the deterministic note from the server's facts (`NO_KEY`); the mechanism the model would pass through (facts → gate → cache) is the one the mock matrix exercises. The mobile Search ticket still reads the design fixture and is outside this desktop pass.

No secret, private query log or raw reasoning is recorded. The rate limiter is an in-process counter per requester (30 per minute); a deployment with several instances needs a shared quota before it can be called a quota.
