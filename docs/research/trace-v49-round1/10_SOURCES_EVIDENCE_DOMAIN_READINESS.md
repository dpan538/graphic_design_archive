# Sources and Evidence Domain Readiness

The object→source bridge is complete internally; the evidence chain after it is empty. Sources/evidence is therefore the least complete public domain, despite broad raw source metadata.

| Stage | Total records | Public-object coverage / objects ≥1 / objects 0 | Median / P95 / max per object | Stable ID | Public-safe fields | Rights/publication constraint |
|---|---:|---:|---:|---|---|---|
| public archive object | 7,995 | 7,995 / 7,995 / 0 | 1 / 1 / 1 | public surface ID | sealed ID/title | held excluded |
| raw source record association | 15,923 | 7,995 / 7,995 / 0 | 1 / 1 / 1 | internal UUID | none without serializer | raw payload/URL restricted |
| normalized source document/version | 0 | 0 / 0 / 7,995 | 0 / 0 / 0 | schema UUID, no rows | none | not populated |
| assertion | 0 | 0 / 0 / 7,995 | 0 / 0 / 0 | schema UUID, no rows | none | not populated |
| evidence item/occurrence | 0 | 0 / 0 / 7,995 | 0 / 0 / 0 | schema UUID, no rows | none | not populated |
| locator/citation evidence | 0 | 0 / 0 / 7,995 | 0 / 0 / 0 | no public evidence ID | generic release citation is not object evidence | no serializer |
| claim/qualification/challenge | 0 | 0 / 0 / 7,995 | 0 / 0 / 0 | schema URN, no rows | none | not populated |
| semantic relation | 0 | 0 / 0 / 7,995 | 0 / 0 / 0 | schema URN, no rows | none | not populated |

Required ratios are consequently all zero: claims with evidence, relations with claims, relations with evidence, claims with locator/citation, and fully evidence-complete relations.

Raw public candidates have 15 source labels. They are concentrated: the largest accounts for 3,505/7,995 objects (43.84%), top five for 7,326 (91.63%), and HHI is 0.288151. Purely proportional future review samples would underrepresent rare sources.

The retained v48 SQLite contains 12,635 legacy source-document IDs (12,549 single-object, 86 shared; maximum fanout 1,963). Of these, 4,711 are public-bearing and 7,924 held-bearing, with no mixed IDs. This is a capacity/reconciliation diagnostic only, not a v49 evidence population or publication source.

## Prohibited derivations

- citation exists ⇒ supports;
- multiple sources ⇒ stronger truth;
- more evidence rows ⇒ greater historical certainty;
- object/source bridge ⇒ evidence-complete claim;
- shared source ⇒ object-to-object semantic relation.

The type foundation preserves source, source record, evidence occurrence, citation, locator, claim links, qualifications/challenges, provenance activity, and semantic edges as distinct categories. Its source fixture is explicitly synthetic and contains no URL, locator, wording, UUID, or held record.

```text
SOURCES_V1=READY_FOR_PREPROGRAM_ONLY
```

This label authorizes only the disconnected types/pure functions. A public evidence-bearing Sources V1 remains `NOT_SUPPORTED` until a future governed data release and safe public serializer exist.
