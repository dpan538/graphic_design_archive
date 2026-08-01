# TRACE visualization v48 — reference study and evidence-safe mapping

Status: **accepted refinement on the isolated visualization branch**

Date: 2026-08-01

## Core decision: three questions, three diagrams

The references are not combined into one overloaded network. They define three
separate research readings of the selected object. A single compact mode button
opens on hover, focus or click and presents one icon per reading:

| Diagram | One research question | Included edge family | Explicit exclusions |
| --- | --- | --- | --- |
| Medium/context metro | In which media and documented contexts is the object situated? | `medium_context` | source, place, date and influence edges |
| Time/geography map | When and where is the object recorded? | `time_place` plus frozen object year/region | source, medium, movement, diffusion and influence |
| Source rooted tree | Which evidence sources and provenance routes document the object? | `source_provenance` | medium, place, date and influence edges |

All three occupy the full TRACE research canvas. Selection, object metadata,
layer controls and the exact relation table live in a left information drawer
that can be opened or collapsed without resizing the meaning of the diagram.

## Reference 1: schematic transit routes

The useful grammar is a small number of deterministic trunks and discrete
stations. It is applied only to medium and documented context:

| Transit grammar | TRACE meaning |
| --- | --- |
| Interchange | selected object |
| Trunk | one actual `medium_context` relation label |
| Station | one linked evidence node |
| Station code | stable local index in this view |

Parallel lines make relation types comparable without a physics layout. A line
connects stations to the selected object; it never asserts that adjacent
stations caused or influenced one another.

## Reference 2: rooted source tree

The root form is reserved for provenance. The selected object is the root,
actual source/provenance relation labels are first-order branch hubs, and their
documented evidence nodes are leaves. Line width indicates hierarchy only, not
evidence strength. The tree does not manufacture intermediate people, places,
movements or genealogical influence.

## Reference 3: time axis plus geography

The map uses a restrained Equal Earth world geometry. It highlights only a
country outline that can be matched from the frozen normalized object region.
The shared 1800–2030 axis marks the recorded object year.

Evidence boundary:

- a country fill is a normalized regional category, not an object coordinate;
- non-country categories such as `Global / transnational` remain textual and
  do not receive a guessed outline;
- no museum location, creator nationality, search term or guessed centroid is
  substituted;
- map proximity never creates movement, diffusion or influence edges.

The basemap is a derivative display aid from `world-atlas` / Natural Earth
Admin 0 at 1:110m. `d3-geo` performs projection and SVG path generation, and
`topojson-client` reads the topology. These packages do not modify the frozen
database or introduce new object evidence.

## Fullscreen and responsive behavior

- Desktop: one diagram fills the available viewport; the mode button is
  centered above the canvas and global/object navigation remains reachable.
- Information: the left drawer contains search, frozen-layer filters, object
  facts, source links, the zero-influence notice and the exact relation table.
- Mobile: the large SVG is replaced by a labelled evidence index and concise
  geographic text. The drawer becomes a nearly full-width progressive panel.
- Keyboard and no-graphic use: mode choices are radio-menu items, diagram nodes
  are links, all states have text labels, and the drawer/table provides the
  non-graphic route back to evidence.
