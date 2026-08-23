# Curatorial structure census

## Classification result

The registry distinguishes population from governance and safety. Counts below are sanitized aggregate receipts; duplicate representations are not summed.

| Structure | Population | Classification summary | Containers | Memberships | Public coverage | Held coverage |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Accepted semantic relations | empty | public governed | 0 | 0 | 0 | 0 |
| Appendices | populated | legacy, internal, unsafe | 15,453 | 15,453 | 7,995 | 7,458 |
| Bookmarks | empty | legacy, internal | 0 | 0 | 0 | 0 |
| Compound-child references | populated | legacy, internal, unsafe | 15 | 132 | 15 | 0 |
| Folder membership | populated | candidate, legacy, internal, unsafe | 185 | 47,982 | 7,995 | 7,928 |
| Folder-related graph | populated | candidate, legacy, internal, unsafe | 185 | 0 object memberships; 2,016 directed references / 1,008 edges | 0 | 0 |
| Governed Context representations | populated | public governed | 25 | 16,106 | 7,995 | 0 |
| Governed Spacetime geography | populated | public governed | 93 | 7,996 | 7,995 | 0 |
| Governed TRACE projection | empty | public governed, known fail-closed | 0 | 0 | 0 | 0 |
| Legacy trace branches | populated | legacy, internal, unsafe | 85 | 80,093 | 7,995 | 7,928 |
| Legacy trace trees | populated | legacy, internal, unsafe | 30 | 15,923 | 7,995 | 7,928 |
| Object-to-trace-edge membership | populated | legacy, internal, unsafe | 126,822 | 126,822 | 7,995 | 7,928 |
| Reading notes | populated | legacy, internal, unsafe | 354 | 47,982 | 7,995 | 7,928 |
| Registration cards | populated | legacy, internal, unsafe | 185 | 47,982 | 7,995 | 7,928 |
| Research dossiers | populated | legacy, internal, unsafe | 15,923 | 46,961 | 7,995 | 7,928 |
| Sealed public folder-membership release | empty | candidate | 0 | 0 | 0 | 0 |
| Source-collection membership | populated | candidate, legacy, internal, unsafe | 3,750 | 15,908 | 7,980 | 7,928 |
| Source-document assignment | populated | legacy, internal, unsafe | 12,635 | 15,923 | 7,995 | 7,928 |
| SQLite trace edges | populated | legacy, internal, unsafe | N/A | 0 memberships; 255,695 structure rows | 0 | 0 |
| SQLite trace nodes | populated | legacy, internal, unsafe | N/A | 0 memberships; 97,889 structure rows | 0 | 0 |

`POPULATED` is an existence claim, not a publication decision. `UNSAFE` means the raw representation cannot be copied into a public aggregate package.

## Canonical folder-membership census

| Cohort | Objects | Memberships | Nonempty containers | Memberships/object P50 / P95 / max | Nonempty container size P50 / P95 / max | Raw pair events |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| Public | 7,995 | 24,102 | 118 | 3 / 3 / 5 | 11.5 / 547.55 / 7,105 | 43,891,194 |
| Held | 7,928 | 23,880 | 157 | 3 / 3 / 4 | 20 / 407.8 / 6,082 | 33,430,602 |
| Combined | 15,923 | 47,982 | 185 | 3 / 3 / 5 | 29 / 570 / 10,010 | 120,229,777 |

All 7,995 public objects have curated membership; all have multiple memberships. Public folder-type assignments are medium 7,995, theme 7,996, movement 115 across 110 objects, and region 7,996. The 118 public nonempty containers are drawn from the 185 known containers; 67 known containers have zero public membership.

## Distribution coverage beyond folders

Every populated structure has either P50/P90/P95/P99/max distributions or an explicit not-applicable reason:

- appendices cover 7,995 public and 7,458 held objects; all 15,453 appendix containers have size one;
- reading notes contain 354 containers and 47,982 memberships; 169 containers are empty, while size P50/P95/P99/max is 1/351/3,408.34/10,010;
- compound parents cover 15 public objects and no held object; container size P50/P95/max is 3/26.2/64;
- object-trace-edge membership covers 7,995 public and 7,928 held objects; public memberships/object P50/P95/max is 11/16/31;
- graph memberships/object is not applicable because the graph describes container-to-container adjacency, not object membership;
- governed Context/Spacetime held distributions are not applicable because those projections are public-only;
- SQLite trace nodes and edges are non-container graph structures, so container-size and object-membership distributions are not applicable.

Every applicable public and held memberships-per-object distribution also records exact `multipleCount` (objects with more than one membership). Examples: folder membership 7,995 public / 7,928 held; legacy trace branches 7,993 / 7,928; research dossiers 7,995 / 7,458; governed Spacetime geography 1 public / held not applicable; appendices 0 / 0. Non-object graph structures carry a not-applicable rationale instead of a synthetic multiple count.

Empty structures retain an explicit empty-release rationale rather than fabricated zero-valued membership distributions.

## Governance decision

Raw curated co-membership may be analyzed as `STRUCTURAL_DIAGNOSTIC`. It does not become a Context representation, historical relation, semantic relation, or evidence of influence. A future public Exploration feature requires a separately governed derived release; it cannot read these internal structures directly.
