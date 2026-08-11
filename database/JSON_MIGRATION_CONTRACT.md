# v48 JSON to v49 migration contract

This contract describes the separately authorized population phase. Phase 2A
does not execute it.

## Authority

The sole canonical migration input is the frozen v48 candidate JSON whose
SHA-256 is
`b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`.
SQLite remains immutable reconciliation evidence; manifests remain integrity
evidence; Search, atlas, catalog and TRACE shards remain derived products.
None may create canonical rows.

## Required batch preconditions

1. Register the frozen candidate asset through the migrator path with its exact
   byte length and SHA-256.
2. register a reviewed mapping version whose delimiter policy is exactly
   `preserve_no_automatic_split`;
3. create one migration batch binding the asset SHA and mapping version;
4. enumerate the candidate `surfaces` array deterministically without nested
   expansion, merge, split or automatic deduplication;
5. preserve each raw record and each source field occurrence before mapping;
6. account for every input occurrence in `raw.legacy_surface_ledger` as
   candidate, accounted, held or rejected;
7. create one conservative operational archive object for each accounted
   legacy surface in the v49.0 baseline;
8. record every parse/classification delta in the fail-closed queue.

The migration verifier, not DDL, enforces:

```text
LEGACY_INPUT_SURFACES=15923
ACCOUNTED_INPUT_SURFACES=15923
UNACCOUNTED_INPUT_SURFACES=0
BASELINE_ARCHIVE_OBJECTS=15923
RESEARCH_ELIGIBLE_OBJECTS=7995
HELD_OBJECTS=7928
```

The value 20,000 is not a parity gate, quota, check constraint or collection
target.

## Research and TRACE rules

- Missing candidate `trace.tier` stays held; SQLite's legacy normalization to
  `source_verified` cannot be copied back into canonical state.
- Unknown relation labels create raw literals and held relation-type review
  cases only.
- No legacy projection edge becomes a canonical semantic relation. In
  particular, the 255,695 legacy graph edges are not migration input.
- Accepted relations begin at zero and require separately reviewed canonical
  evidence. Empty TRACE projections remain valid release output.
- Derived Search and TRACE generators receive a sealed release identity and
  have no database grant that writes canonical schemas.

## Visual rules

Legacy visual references are migrated as typed references, providers, locators
and object bridges with unknown/held states preserved. No positive delivery
permission is inferred from URL presence, IIIF, HTTP status or thumbnail
availability. The baseline's zero positive-rights coverage is legal.

Third-party pixel and image-service locators remain internal unless a later
reviewed delivery decision satisfies the database `REMOTE_IMAGE` constraints.
No third-party image binary is imported.

## Population completion receipt

The later migration must report asset hashes, batch and mapping IDs, all count
units, ID-set hashes, duplicate candidates, delimiter risks, null/orphan counts,
held/rejected preservation, zero unclassified rows, test fixture residue zero,
and the sealed release IDs/hashes. Population and freeze are distinct gates.
