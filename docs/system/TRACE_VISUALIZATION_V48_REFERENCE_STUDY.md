# TRACE visualization v48 — reference study and evidence-safe mapping

Status: **accepted refinement on the isolated visualization branch**

Date: 2026-08-01

## Reference 1: schematic transit routes

The useful feature is not the transport theme itself. It is the way a small
number of strongly differentiated trunks makes many discrete stops readable
without requiring a physics layout.

TRACE mapping:

| Transit grammar | TRACE meaning |
| --- | --- |
| Interchange | selected object root |
| Green P route | source and provenance evidence |
| Blue T route | time and object-place evidence |
| Red M route | medium and documented context |
| Station | one evidence node with a return URL |
| Station code | stable local index within the selected object view |
| Route key | full node label, edge label, direction and review state |

The lines are categorical organizers. They do not mean that one station caused
or influenced the next station. All three routes meet only because they
document the selected object.

This mode is preferred over a force graph because every station has a known
lane, the layout is deterministic, and the diagram remains comparable between
objects.

## Reference 2: rooted generative tree

The useful feature is a single origin with progressively lighter branches.
TRACE can use that hierarchy without treating line weight as evidence strength:

1. the object is the root;
2. relation families are first-order branch hubs; and
3. actual evidence nodes are leaves.

Line width indicates layout depth only. Leaf labels retain relation direction
and actual edge vocabulary. The tree never manufactures intermediate people,
places, movements or influence relations.

The rooted tree is better than the route map when the research question is
“what documents this one object?” The route map is better when comparing the
balance of evidence families and scanning many stations.

## Reference 3: time axis plus geography

The described third reference was not attached. The frozen v48 schema was
therefore audited before choosing a map form.

The database has normalized object `region` values but no publishable latitude,
longitude, geometry or object-level geocode. A geographic basemap would require
a new curated coordinate sidecar. Using museum location, creator nationality,
search terms or guessed centroids would violate the freeze evidence boundary.

The accepted v48 form is a chronogeographic route table:

- horizontal position is the real decade axis;
- each horizontal rail is one frozen normalized object region;
- a station exists only when active objects occur in that region and decade;
- station area is log-scaled active-object count; and
- selecting a station opens the exact region/decade object filter.

The rail is a categorical axis, not a claim of uninterrupted development,
diffusion or influence. The exact count matrix remains available as a text/table
fallback.

## Conditions for a future geographic map

A true map should be added only after a separately reviewed sidecar provides:

- object-level coordinates or an explicit region geometry identifier;
- coordinate provenance and precision;
- a distinction between object place, circulation place and institution place;
- review/hold state for ambiguous geometry; and
- a rule forbidding map proximity from generating TRACE or influence edges.

That sidecar would be a new candidate version or derivative evidence layer. It
must not edit the frozen v48 database in place.
