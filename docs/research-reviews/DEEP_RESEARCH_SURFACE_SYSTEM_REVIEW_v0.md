# Deep Research Surface System Review v0

Date: 2026-05-30

Reviewed reports:

- `Archive Production Rulebook for a Rights-Aware Research Gateway to Modern Graphic Design History.docx`
- `File Naming and Archival Storage Rulebook for a Rights-Aware Graphic Design History Archive Index.docx`
- `Surface Taxonomy Rulebook for a Rights-Aware Graphic Design History Archive.docx`
- `Rights-Aware Archive Box Interface Framework for Modern Graphic Design History.docx`

Generated implementation documents:

- `ARCHIVE_PRODUCTION_RULEBOOK_v0.md`
- `FILE_NAMING_AND_ARCHIVAL_STORAGE_v0.md`
- `SURFACE_TAXONOMY_RULEBOOK_v0.md`
- `ARCHIVE_BOX_INTERFACE_FRAMEWORK_v0.md`

## Key Decisions Confirmed

1. Time is a sorting axis, not a container.
2. The four primary folder types are Region, Theme, Medium, and Movement.
3. Folders are aggregation/filter views and do not own records.
4. Folder type can own color, but folder color must not change record layout.
5. Main sheets require a completeness threshold of roughly 60% plus essential gates.
6. Below-threshold records remain visible as cards, fallback stubs, proposed cell items, or unassigned research items.
7. Capture batches are production candidate pools, not disposable tests.
8. `IMG00` through `IMG04` are image presence/display states, separate from page size.
9. `IMG04` means no image frame, not a copyright level.
10. Public surfaces must keep source return, rights status, uncertainty, and citation visible.

## Report-to-Rule Mapping

| Report | Main contribution | Project document |
|---|---|---|
| Archive Production Rulebook | State machine, promotion rules, IMG evidence rules, review gates. | `ARCHIVE_PRODUCTION_RULEBOOK_v0.md` |
| File Naming and Archival Storage | ID strategy, layered storage, raw/canonical/derived/build/release separation. | `FILE_NAMING_AND_ARCHIVAL_STORAGE_v0.md` |
| Surface Taxonomy Rulebook | Generated surface types and MVP/later surface sets. | `SURFACE_TAXONOMY_RULEBOOK_v0.md` |
| Archive Box Interface Framework | Layout modules, folder cover, sheet/card/stub behavior, threshold model. | `ARCHIVE_BOX_INTERFACE_FRAMEWORK_v0.md` |

## Immediate Implementation Consequences

The next practical work should not be another broad capture batch. It should be rule integration:

- Add capture row alias support so current `ECAP001` rows can later migrate toward `CB001-R0001`.
- Add or confirm fields for completeness score, surface eligibility, proposed cell state, and assignment confidence.
- Create a surface generation input table or JSON payload that Cursor can consume without reading raw capture rows directly.
- Define fixed template IDs for folder cover, main sheet, text sheet, card, fallback stub, proposed cell item, and unassigned item.
- Keep source review and rights review gates separate from IMG detection.

## Open Design Questions

1. Should `PC01`-style proposed cells be visible in the public interface immediately, or only after editorial acceptance?
2. Should `unassigned research item` appear inside all plausible folders or only in a global unassigned tray plus search?
3. Should `IMG01` be used in the first public release, or should it stay internal until source-specific thumbnail terms are reviewed?
4. Should `Registration Card` be public in MVP, or first implemented as internal review metadata?
5. How much visual color should each folder type receive without breaking the 1-bit archive paper language?

## Recommended Next Step

Write a frontend handoff spec for the archive box system:

- public route map;
- required API payload shape per surface;
- surface template IDs;
- fixed layout modules;
- folder color/token rules;
- completeness-to-surface decision fields;
- placeholder global search behavior.

This should happen before more capture or before Cursor begins page implementation.
