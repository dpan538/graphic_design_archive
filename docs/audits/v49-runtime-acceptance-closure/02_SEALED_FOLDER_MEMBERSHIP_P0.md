# P0: no sealed folder membership projection

## Bounded evidence

`database/migrations/007_release_copy_integrity.sql` defines
`release.research_folder_projection` with four fields only:

```text
research_release_id
folder_id
folder_token
label
```

It has no object/member key. The only official builder,
`release.copy_research_folder_to_draft` in
`database/functions/009_projection_inventory_builders.sql`, inserts those
same four fields from mutable `research.folder`.

The release snapshot contains `research_release_object`, but it has no
folder-member reference. `provenance.assignment_folder_membership` is outside
the release snapshot. The existing schema therefore cannot answer an exact
release-pinned `folder -> members` request after a provider resolves an exact
pair.

## Decision

The requested forward-only `010` is limited to `api_v1` safe views/functions
and grants; it may not add the missing release snapshot table or alter the
release/Seal/CAS protocol. A view that joins the mutable provenance table
would be noncompliant. This is a P0 contract/model blocker.

Required next authorization: design and add a forward-only, release-owned
folder-membership snapshot through the release protocol, then replay and seal
a new compact fixture. That is materially outside this closure instruction.
