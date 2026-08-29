# Evidence-search protocol

## Version and scope

Protocol: `trace-exploration-association-search-v2`. The protocol is applied only when complete local Round 9–16 evidence is insufficient. It is a discovery and falsification aid, not an automatic association generator.

## Query

For canonical labels A and B, issue one stable Crossref Works query containing quoted A, quoted B, and `graphic design OR design history`. Request at most five ranked metadata records and select identifiers, title, author, date, container/publisher, type, URL, link, subject, and deposited abstract when present. Queries are sequential and respect the current public list-request limit. HTTP 429/5xx responses use bounded exponential retry and remain visible in the query log.

The exact request URL, timestamp, HTTP status, result count, rate-limit headers, candidate identifiers, and response hash are recorded. Full responses are cached during the run; the committed query log and evidence ledger retain all evidence-bearing fields without secrets. Crossref metadata is used because the official REST API permits public access and structured bibliographic discovery; a search result or title match alone is never evidence.

## Candidate-source review

Each returned record receives one decision:

- `ACCEPT_ASSOCIATION_EVIDENCE`: source text/abstract and locator explicitly support a bounded generic association between the two exact senses in a design-historical context;
- `REJECT_METADATA_DISCOVERY_ONLY`: bibliographic metadata identifies a possible source but no evidence-bearing text is available;
- `REJECT_COOCCURRENCE_ONLY`: both labels occur but no historical/contextual association is established;
- `REJECT_TERM_MISMATCH`: one or both exact senses are absent or lexical matching is misleading;
- `REJECT_DOMAIN_MISMATCH`: not design history or a directly relevant design-history domain;
- `REJECT_SCOPE_CONFLICT`: source senses conflict with the frozen vocabulary scopes;
- `REJECT_DUPLICATE_SOURCE`: already reviewed through a governed registry;
- `REJECT_NON_SCHOLARLY_OR_UNVERIFIABLE`: source type/metadata/locator cannot clear the protocol.

Automated discovery cannot promote an association. A new pass requires an explicit reviewed evidence row containing the evidence-bearing text location, source identity, D1–D7 justification, qualification, and non-claims. Otherwise the conservative final status is inactive. This prevents search ranking, snippets, frequency, or database co-occurrence from becoming historical evidence.

## Source-supported final policy

`ACTIVE_SOURCE_SUPPORTED` is permitted only for a directly inspected, stable primary or institutional design-history source that explicitly supports the bounded generic proximity; it must clear the same D1/D5/D7 and ordinal threshold and carry a final-policy reason. It does not claim independent academic endorsement. The status may not contain “pending” language.

## Reproducibility boundary

External result ordering can change. Raw query responses are therefore hashed and timestamped, while deterministic downstream censuses consume the frozen reviewed query/evidence ledgers. Clean-worktree reproduction replays the frozen ledgers, not a new live web search.

