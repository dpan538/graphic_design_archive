# Corpus boundary validation

## Evidence state

`DOCUMENT_STATE=SEALED`

## Authoritative eligibility source

The sole public/held authority is
`docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv`, SHA-256
`48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01`.
The frozen source commit is
`580587a74f400d8a04d995937f4efb31e6621dd8`.

The ledger reconciliation is:

```text
CANONICAL_OBJECT_COUNT=15923
PUBLIC_OBJECT_COUNT=7995
HELD_OBJECT_COUNT=7928
OVERLAP_COUNT=0
UNCLASSIFIED_COUNT=0
```

Eligibility is checked before canonical text is retained or normalized. A
rejected lookup reports only that the object is unavailable to the public NLP
cohort; it does not reveal whether the input was held or unknown.

## Frozen input pins

| Artifact | SHA-256 |
| --- | --- |
| migration ledger | `48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01` |
| SQLite source | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` |
| canonical public surfaces | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` |
| Context records | `c767b9661e4cb417cfaae3948d7ed2b974fc88e1dcc9a3686eae90ae8610a9e7` |
| Context manifest | `ff8ebc15eeb95407b6b6b274dd2fc69ce4c3c183bb2f6a7e7f261c028b96f92c` |
| Spacetime records | `0f4720672f1e906301e3966dc3970737e3a1e459b27317b47018a2e6445c3dec` |
| Spacetime manifest | `93e88157865d987376ec8997e94a4101353038cf792e665d35e4c50b1c4384ec` |
| Round 6 review receipt | `2178df8e22d367cf9ce391d3dfab9f579d7371d4a1aefa1d0b389eb9132d044f` |
| Round 6 checksum ledger | `5774163988796716aa80be90268f1fa7e428ae3fd85a88424db54f6aaa3bc110` |

Context and Spacetime projection hashes are
`825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb`
and `f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06`.

## Corpus build receipt

The deterministic builder currently emits 7,995 sorted, unique public document
identities, with no held identity. It produces:

```text
TITLE_ASPECT_OBJECT_COUNT=7995
SUBJECT_ASPECT_OBJECT_COUNT=7838
OBJECT_DESCRIPTION_ASPECT_OBJECT_COUNT=0
SOURCE_NARRATIVE_ASPECT_OBJECT_COUNT=7431
APPROVED_COMPOSITE_OBJECT_COUNT=7995
URL_REMOVED_COUNT=209
CORPUS_DOCUMENT_RECEIPT_SHA256=69aa8f290f7390bdb8ce7c0a3cf4ecdfb7426c908804bf48f9126c0eec4fdac8
```

One disallowed-control value is held out of an otherwise populated optional
aspect. It does not remove the public document identity or create substitute
text.

## Fail-closed checks

The final verifier must prove:

- corpus IDs equal the authoritative eligible-ID set exactly;
- corpus IDs are sorted and unique;
- held-ID intersection is empty;
- Context and canonical public IDs reconcile exactly;
- every public document has title and title-only composite;
- optional aspects contain only their authoritative registered field;
- no private token, internal UUID, file URL, or held identity appears;
- the corpus output path is local/untracked; and
- no committed file contains the full generated corpus.

```text
NLP_CORPUS_BOUNDARY_TESTS=PASS
PUBLIC_ID_SET_SHA256=b64a6dcb10a8ffdd52cf9bf7a7a8918de012b76805823a79afae71dcf2c07d05
HELD_ID_INTERSECTION_COUNT=0
COMMITTED_FULL_CORPUS_FILE_COUNT=0
```

Any nonzero held intersection or committed full-corpus count is a hard stop.
