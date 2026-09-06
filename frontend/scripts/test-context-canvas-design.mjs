/* Context Canvas design contract (FRONTEND_DESIGN_DECISION.md §7g): the
   page's own pure modules against the governed projection —
   the three connection wordings, the connectors (one class, object to
   representation, no arrowheads, none for a dimension not recorded,
   count = visible representations), the four layouts' invariance (the
   same ids, fields and wording under every preset), the real 3 / 4 / 5
   node objects and the synthetic stress fixture, the research-card
   export (labels as titles, no full hash or internal identifier in
   sight, the binding in <desc>), and the clipboard tables. */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const require = createRequire(import.meta.url);
const jiti = require("jiti")(fileURLToPath(import.meta.url), {
  interopDefault: true,
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-marker.mjs"),
  },
});
const route = join(frontendRoot, "src/app/trace/context-canvas");
const { getGovernedContextExampleOptions, getGovernedContextLandingRecord, getGovernedContextSampleOptions, lookupGovernedContextDataset, searchGovernedContextObjects } = await jiti.import(
  join(frontendRoot, "src/features/trace-v49/context/governed/reader.server.ts"),
);
const { adaptPublicContextDatasetForCanvas } = await jiti.import(
  join(frontendRoot, "src/features/trace-v49/context/governed/canvas.ts"),
);
const arrange = await jiti.import(join(route, "lib/arrange.ts"));
const presentation = await jiti.import(join(route, "lib/presentation.ts"));
const card = await jiti.import(join(route, "lib/export-card.ts"));
const content = await jiti.import(join(route, "lib/content.ts"));
const stress = await jiti.import(join(route, "lib/stress-fixture.server.ts"));

const WORDING = Object.freeze({ medium: "classified as", theme: "themed as", movement_context: "curated within" });
const PRESETS = ["overview", "focus", "columns", "dense"];
let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks += 1; };

const defaultId = getGovernedContextSampleOptions()[0].stableId;
const REAL = [
  { id: defaultId, nodes: 3 },
  { id: "SURF-CHWCONTEMP2026V1R0006", nodes: 4 },
  { id: "SURF-COMPOUND-ARUNDEL-SOCIETY-CHROMOLITHOGRAPH-COPIES", nodes: 4 },
  { id: "SURF-LOCTRACE2026R00867", nodes: 5 },
];

function describe(publicDataset, selectedTermIndex = 0) {
  const canvas = adaptPublicContextDatasetForCanvas(publicDataset);
  const reps = canvas.metadata.governedContext.representations;
  const object = {
    title: publicDataset.selectedRecord.title,
    stableId: publicDataset.selectedRecord.surfaceId,
    ...publicDataset.selectedRecord.rootMetadata,
  };
  const visibleIds = new Set(reps.map((r) => presentation.termEntityId(r.termId)));
  const model = presentation.buildPresentation({
    object, representations: reps, visibleIds, boundary: content.BOUNDARY,
    releaseId: publicDataset.release.researchReleaseId, canvasName: content.NAME,
  });
  const terms = model.dimensions.flatMap((d) => d.items.map((i, k) => ({
    entityId: i.entityId, label: i.label, kind: i.kind, wording: i.representation.connectionLabel,
    selected: d.kind === "theme" && k === selectedTermIndex,
  })));
  return { canvas, reps, model, terms, publicDataset };
}

function checkConnectionContract({ reps }) {
  for (const r of reps) {
    check(r.connectionLabel === WORDING[r.kind], `wording for ${r.kind} is the contract's (${r.connectionLabel})`);
  }
}

function checkLayouts({ reps, terms, model }, expectedNodes) {
  const rootId = "test:object";
  const totals = Object.fromEntries(model.dimensions.map((d) => [d.kind, d.items.length]));
  const wording = {};
  for (const t of terms) { wording[t.entityId] = t.wording; wording[t.kind] = t.wording; }
  let idsBefore = null;
  for (const preset of PRESETS) {
    const layout = { preset, focusKind: terms[0]?.kind ?? "medium" };
    const positions = arrange.arrangeWith(rootId, terms.map((t) => ({ id: t.entityId, kind: t.kind })), layout);
    const ids = Object.keys(positions).sort();
    check(ids.length === reps.length + 1, `${preset}: every representation and the object have a position`);
    if (expectedNodes) check(ids.length === expectedNodes, `${preset}: ${expectedNodes} nodes`);
    if (idsBefore) check(JSON.stringify(ids) === JSON.stringify(idsBefore), `${preset}: the same ids as the previous layout`);
    idsBefore = ids;
    const nodes = [{ id: rootId, isRoot: true, kind: null, position: positions[rootId] }, ...terms.map((t) => ({ id: t.entityId, isRoot: false, kind: t.kind, position: positions[t.entityId] }))];
    const fields = arrange.fieldsOf(nodes, totals, layout);
    check(fields.length === 3, `${preset}: three fields`);
    for (const f of fields) {
      const expected = totals[f.kind] === 0 ? "not_recorded" : "filled";
      check(f.state === expected, `${preset}: ${f.kind} field is ${expected}`);
      if (f.state !== "filled") check(f.compact === true, `${preset}: an empty field is compact`);
    }
    /* chips never overlap one another or the object */
    const boxes = nodes.map(arrange.boxOf);
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      check(!arrange.boxesOverlap(boxes[i], boxes[j]), `${preset}: no two items overlap`);
    }
    const connectors = arrange.connectorsOf(nodes, fields, layout, wording);
    const objectBox = arrange.boxOf(nodes[0]);
    const labelBox = (c) => {
      const w = arrange.labelWidth(c.label);
      return c.labelVertical
        ? { x: c.labelAt.x - arrange.LABEL_H / 2, y: c.labelAt.y - w / 2, width: arrange.LABEL_H, height: w }
        : { x: c.labelAt.x - w / 2, y: c.labelAt.y - arrange.LABEL_H / 2, width: w, height: arrange.LABEL_H };
    };
    const boxDist = (a, b) => Math.hypot(Math.max(b.x - (a.x + a.width), a.x - (b.x + b.width), 0), Math.max(b.y - (a.y + a.height), a.y - (b.y + b.height), 0));
    const through = (a, b, box) => {
      const sx = Math.min(a.x, b.x), ex = Math.max(a.x, b.x), sy = Math.min(a.y, b.y), ey = Math.max(a.y, b.y);
      return ex > box.x + 0.5 && sx < box.x + box.width - 0.5 && ey > box.y + 0.5 && sy < box.y + box.height - 0.5;
    };
    const onObject = (p) => p.x >= objectBox.x - 0.01 && p.x <= objectBox.x + objectBox.width + 0.01 && p.y >= objectBox.y - 0.01 && p.y <= objectBox.y + objectBox.height + 0.01;
    const covered = new Map();
    for (const c of connectors) {
      check(onObject(c.points[0]), `${preset}: every wire starts at the object (no term-term, no object-object)`);
      check(c.label === WORDING[c.kind], `${preset}: the wire carries the contract's wording`);
      check(totals[c.kind] > 0, `${preset}: no wire for a dimension not recorded`);
      check(c.points.length >= 2 && c.points.length <= 4, `${preset}: a wire is a straight or orthogonal run`);
      for (let i = 1; i < c.points.length; i++) {
        const a = c.points[i - 1], b = c.points[i];
        check(Math.abs(a.x - b.x) < 0.01 || Math.abs(a.y - b.y) < 0.01, `${preset}: every run is horizontal or vertical`);
      }
      const end = c.points[c.points.length - 1];
      const firstChip = arrange.boxOf(nodes.find((node) => node.id === c.chipIds[0]));
      const onChipEdge = end.x >= firstChip.x - 0.01 && end.x <= firstChip.x + firstChip.width + 0.01 && end.y >= firstChip.y - 0.01 && end.y <= firstChip.y + firstChip.height + 0.01;
      check(onChipEdge, `${preset}: the wire ends on its chip, never merely on the field`);
      /* the wording's box keeps 20 px clear of every card and never lies
         on a field's outline other than its own field's */
      const lb = labelBox(c);
      const nearest = Math.min(...boxes.map((box) => boxDist(lb, box)));
      if (nearest < 20) console.log("  wording near a card:", preset, c.id, c.labelAt, nearest);
      check(nearest >= 20, `${preset}: the wording sits at least 20 px from every card`);
      for (const f of fields) if (f.kind !== c.kind) check(!arrange.boxesOverlap(lb, f.box, 0), `${preset}: the wording is never on another field's outline`);
      /* the wire passes through no other field and no card's interior */
      for (let i = 1; i < c.points.length; i++) {
        const a = c.points[i - 1], b = c.points[i];
        for (const f of fields) if (f.kind !== c.kind) {
          if (through(a, b, f.box)) console.log("  wire through a field:", preset, c.id, f.kind);
          check(!through(a, b, f.box), `${preset}: a wire never passes through another field`);
        }
        for (const box of boxes) check(!through(a, b, box), `${preset}: a wire never passes through a card`);
      }
      for (const id of c.chipIds) covered.set(id, (covered.get(id) ?? 0) + 1);
    }
    for (const t of terms) check(covered.get(t.entityId) === 1, `${preset}: ${t.label.slice(0, 20)} is on exactly one wire`);
    /* a drag's determination: a laid-out chip keeps its place; a chip
       dropped away from its field, or the object moved, is put back; a chip
       dropped on a sibling's slot changes places with it */
    const baseline = Object.fromEntries(nodes.map((node) => [node.id, node.position]));
    for (const node of nodes) {
      const outcome = arrange.dropOutcome(nodes, baseline, layout, node.id);
      check(outcome.kind === (node.isRoot ? "put_back" : "keep"), `${preset}: ${node.isRoot ? "the object stays" : "a laid-out chip keeps its place"}`);
    }
    const chip = nodes.find((node) => !node.isRoot);
    if (chip) {
      const away = nodes.map((node) => node.id === chip.id ? { ...node, position: { x: node.position.x + 5000, y: node.position.y + 5000 } } : node);
      const out = arrange.dropOutcome(away, baseline, layout, chip.id);
      check(out.kind === "put_back" && out.reason === "outside_field", `${preset}: a chip dropped away from its field is put back`);
      const sibling = nodes.find((node) => !node.isRoot && node.id !== chip.id && node.kind === chip.kind);
      if (sibling) {
        const onto = nodes.map((node) => node.id === chip.id ? { ...node, position: { x: sibling.position.x + 3, y: sibling.position.y - 2 } } : node);
        const swap = arrange.dropOutcome(onto, baseline, layout, chip.id);
        check(swap.kind === "swap" && swap.otherId === sibling.id, `${preset}: a chip dropped on a sibling's slot changes places with it`);
        if (swap.kind === "swap") {
          check(swap.positions[chip.id].x === sibling.position.x && swap.positions[sibling.id].x === chip.position.x, `${preset}: the two chips exchange their slots exactly`);
        }
      }
    }
    /* wordings never lie on one another (their boxes, as the router sizes them) */
    for (let i = 0; i < connectors.length; i++) for (let j = i + 1; j < connectors.length; j++) {
      const overlap = arrange.boxesOverlap(labelBox(connectors[i]), labelBox(connectors[j]), 2);
      if (overlap) console.log("  overlap:", preset, connectors[i].id, connectors[i].labelAt, connectors[j].id, connectors[j].labelAt);
      check(!overlap, `${preset}: two wordings never overlap`);
    }
  }
}

function checkCard(described, label) {
  const { model, terms, publicDataset } = described;
  for (const preset of PRESETS) {
    const snapshot = card.prepareContextCardSvg({
      presentation: model, terms, layout: { preset, focusKind: terms[0]?.kind ?? "medium" },
      identity: {
        releaseId: publicDataset.release.researchReleaseId,
        manifestSha256: publicDataset.release.researchManifestSha256,
        projectionId: publicDataset.release.contextProjectionId,
        projectionSha256: publicDataset.release.contextProjectionSha256,
      },
      kicker: content.CARD_KICKER, canvasName: content.NAME, record: content.CARD_RECORD, wordmark: content.CARD_WORDMARK,
      site: content.CARD_SITE, notRecorded: content.NOT_RECORDED,
    });
    const svg = snapshot.svg;
    const visible = svg.replace(/<desc>[\s\S]*?<\/desc>/u, "").replace(/<title>[\s\S]*?<\/title>/gu, "");
    check(snapshot.width === 1800 && snapshot.height === 1200, `${label}/${preset}: the card is 1800 × 1200`);
    check(!/<marker|marker-end/u.test(svg), `${label}/${preset}: no arrowheads`);
    check(!visible.includes(publicDataset.release.contextProjectionSha256), `${label}/${preset}: the full projection hash is not printed`);
    check(!visible.includes(publicDataset.release.researchManifestSha256), `${label}/${preset}: the manifest hash is not printed`);
    check(visible.includes(publicDataset.release.contextProjectionSha256.slice(0, 8)), `${label}/${preset}: the fingerprint is printed`);
    check(!/CTX[A-Z]*:/u.test(visible), `${label}/${preset}: no internal identifiers`);
    check(!/\bpublished\b|PUBLISHED|proposed/u.test(visible), `${label}/${preset}: no publication-state language`);
    check(!/System suggests/u.test(visible), `${label}/${preset}: no suggestions`);
    const plain = visible.replace(/<[^>]+>/gu, " ").replace(/\s+/gu, " ");
    check(plain.includes("not historical influence"), `${label}/${preset}: the interpretation boundary`);
    check(svg.includes(`<desc>`) && svg.includes(publicDataset.release.contextProjectionSha256), `${label}/${preset}: the full binding travels in <desc>`);
    for (const t of terms) check(svg.includes(`<title>${t.label.replace(/&/g, "&amp;")}</title>`), `${label}/${preset}: ${t.label.slice(0, 24)} carries its full label`);
    for (const t of terms) check(visible.includes(`>${t.wording}<`), `${label}/${preset}: wording "${t.wording}" on a branch`);
    check(visible.includes("MGDA") && visible.includes("Modern Graphic Design"), `${label}/${preset}: the MGDA mark and wordmark`);
    check(visible.includes(publicDataset.selectedRecord.surfaceId) || visible.includes(publicDataset.selectedRecord.surfaceId.slice(0, 30)), `${label}/${preset}: the stable ID`);
    /* the context map stays inside the ticket's body: the leaves and every
       upright text of the map, through the map's fit transform */
    const mapStart = svg.indexOf('<g transform="translate(');
    const mapEnd = svg.indexOf(`<line x1="${card.STUB_SPLIT}"`);
    const map = mapStart >= 0 && mapEnd > mapStart
      ? /^<g transform="translate\(([-\d.]+) ([-\d.]+)\) scale\(([\d.]+)\)[^>]*>([\s\S]*)$/u.exec(svg.slice(mapStart, mapEnd))
      : null;
    check(map !== null, `${label}/${preset}: the map carries its fit transform`);
    if (map) {
      const ox = Number(map[1]), oy = Number(map[2]), k = Number(map[3]);
      check(k > 0 && k <= 1, `${label}/${preset}: the map is fitted, never enlarged`);
      const body = map[4];
      let low = 0, high = Infinity, left = Infinity, right = 0;
      for (const m of body.matchAll(/<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"/gu)) {
        const y2 = oy + (Number(m[2]) + Number(m[4]) - oy) * k;
        const y1 = oy + (Number(m[2]) - oy) * k;
        const x2 = ox + (Number(m[1]) + Number(m[3]) - ox) * k;
        low = Math.max(low, y2); high = Math.min(high, y1); left = Math.min(left, ox + (Number(m[1]) - ox) * k); right = Math.max(right, x2);
      }
      check(high >= card.TICKET.y + 40 && low <= card.TICKET.y + card.TICKET.height - 40, `${label}/${preset}: the map's plates stay inside the ticket's body (${Math.round(high)}–${Math.round(low)})`);
      check(left >= card.TICKET.x + 40 && right <= card.STUB_SPLIT - 40, `${label}/${preset}: the map's plates stay left of the perforation`);
    }
  }
}

function checkClipboard({ model }, label) {
  const md = presentation.presentationAsMarkdown(model, content.NOT_RECORDED, content.FIELD_SET_ASIDE, content.NAME, content.ARCHIVE_NAME);
  const html = presentation.presentationAsHtml(model, content.NOT_RECORDED, content.FIELD_SET_ASIDE, content.NAME, content.ARCHIVE_NAME);
  check(md.includes("| Dimension | Context |") && md.includes("| Field | Value |"), `${label}: markdown tables`);
  check(html.includes("<table>") && html.includes("<th>Dimension</th>"), `${label}: html tables`);
  check(!/classified as|themed as|curated within|published/u.test(md + html), `${label}: no connection or publication language in the reader's copy`);
  check(md.includes("MGDA · v49 · Context Canvas"), `${label}: the short footer`);
  check(!/[0-9a-f]{40}/u.test(md + html), `${label}: no hash in the reader's copy`);
  for (const d of model.dimensions) {
    if (d.items.length === 0) check(md.includes(`| ${d.word} | Not recorded |`), `${label}: ${d.word} not recorded in the copy`);
    else for (const i of d.items) check(md.includes(`| ${d.word} | ${i.label.replace(/\|/g, "\\|")} |`), `${label}: ${d.word} term in the copy`);
  }
}

/* the deterministic samples: a QA tool — twelve of the public cohort,
   evenly spaced by stable public ID, the first and the last included,
   unique, the same on every call, every one of them loading; an unknown
   ID fails closed */
{
  const { readFileSync } = await import("node:fs");
  const recordsDocument = JSON.parse(readFileSync(new URL("../generated/trace-context-v1/records.json", import.meta.url), "utf8"));
  const ordered = (recordsDocument.records ?? Object.values(recordsDocument).find(Array.isArray)).map((r) => r.selectedRecord.surfaceId);
  const cohort = ordered.length;
  check(cohort === 7995, `the public cohort is ${cohort}`);
  const samples = getGovernedContextSampleOptions();
  check(samples.length === 12, "twelve deterministic samples");
  const expected = Array.from({ length: 12 }, (_, i) => Math.floor((i * (cohort - 1)) / 11));
  check(expected.join(",") === "0,726,1453,2180,2906,3633,4360,5087,5813,6540,7267,7994", "the sample indices are the documented twelve");
  samples.forEach((sample, i) => check(sample.stableId === ordered[expected[i]], `sample ${i} is the record at index ${expected[i]}`));
  check(new Set(samples.map((s) => s.stableId)).size === 12, "sample IDs are unique");
  check(samples[0].stableId === ordered[0] && samples[11].stableId === ordered[cohort - 1], "the cohort's first and last records are covered");
  check(JSON.stringify(getGovernedContextSampleOptions()) === JSON.stringify(samples), "repeated generation is byte-equivalent");
  for (const sample of samples) check(lookupGovernedContextDataset(sample.stableId).ok === true, `sample ${sample.stableId} loads`);
  check(lookupGovernedContextDataset("SURF-NOSUCHRECORD0000").ok === false, "an unknown ID fails closed");
  check(lookupGovernedContextDataset("SURF-").ok === false, "a malformed ID fails closed");
}

/* the examples: picked from the reader-facing objects by fixed criteria,
   never by hand — unique, each loading, the cases the owner named */
{
  const examples = getGovernedContextExampleOptions();
  check(examples.length >= 4 && examples.length <= 6, `${examples.length} examples`);
  check(new Set(examples.map((e) => e.stableId)).size === examples.length, "example IDs are unique");
  const roles = examples.map((e) => e.role);
  for (const role of ["three_contexts", "medium_theme", "two_themes", "two_movements", "other_language"]) check(roles.includes(role), `an example for ${role}`);
  for (const example of examples) {
    const lookup = lookupGovernedContextDataset(example.stableId);
    check(lookup.ok === true, `example ${example.stableId} loads`);
    check(example.title.trim().length > 0 && !/^O\d{5,}$/u.test(example.title.trim()), `example ${example.stableId} has a reader-facing title`);
    const reps = lookup.data.representations;
    const count = (kind) => reps.filter((r) => r.kind === kind).length;
    if (example.role === "three_contexts") check(reps.length === 3 && count("medium") === 1 && count("theme") === 1 && count("movement_context") === 1, "three contexts: one of each kind");
    if (example.role === "medium_theme") check(count("movement_context") === 0 && count("medium") >= 1 && count("theme") >= 1, "medium and theme, no movement");
    if (example.role === "two_themes") check(count("theme") >= 2, "two themes");
    if (example.role === "two_movements") check(count("movement_context") >= 2 && reps.length === 4, "two movements, four contexts");
    if (example.role === "other_language") check(/[^\u0000-\u007f]/u.test(example.title), "a title with letters beyond ASCII");
  }
  /* the search: reader-facing titles, folded; IDs by prefix; record-only
     objects by ID alone */
  const byTitle = searchGovernedContextObjects(examples[0].title.slice(0, 12));
  check(byTitle.some((r) => r.stableId === examples[0].stableId), "a title's first words find the example");
  check(byTitle.every((r) => r.readerFacing), "title search returns reader-facing objects only");
  const other = examples.find((e) => e.role === "other_language");
  const stripped = other.title.normalize("NFD").replace(/[\u0300-\u036f]/gu, "").slice(0, 10);
  check(searchGovernedContextObjects(stripped).some((r) => r.stableId === other.stableId), "diacritics do not matter to the search");
  const byId = searchGovernedContextObjects(examples[1].stableId.slice(0, 14).toLowerCase());
  check(byId.some((r) => r.stableId === examples[1].stableId), "an ID prefix, any case, finds the record");
  const opaque = getGovernedContextSampleOptions().find((s) => /^O\d{5,}$/u.test(s.title.trim()));
  if (opaque) {
    check(searchGovernedContextObjects(opaque.title.trim()).every((r) => r.stableId !== opaque.stableId), "an opaque title is not found by words");
    check(searchGovernedContextObjects(opaque.stableId).some((r) => r.stableId === opaque.stableId && r.readerFacing === false), "a record-only object opens by its exact ID");
  }
  check(searchGovernedContextObjects("a").length === 0 && searchGovernedContextObjects("").length === 0, "one letter or nothing searches nothing");
  check(searchGovernedContextObjects("the", 8).length <= 8, "the limit holds");
}

/* the production UI never lists the QA samples as a reader's choice */
{
  const chooser = readFileSync(join(route, "desktop/ObjectChooser.tsx"), "utf8");
  check(!/Deterministic public samples/u.test(chooser) && /qaSamples && qaSamples\.length > 0/u.test(chooser), "the QA samples stand behind their own gate in the chooser");
  const page = readFileSync(join(route, "page.tsx"), "utf8");
  check(/process\.env\.NODE_ENV !== "production" \|\| query\.qa === "1"/u.test(page), "the QA samples are development or ?qa=1 only");
  check(/parsed\.kind === "default" && preview === null[\s\S]*cookies\(\)[\s\S]*redirect\(`\/trace\/context-canvas\?record=/u.test(page), "without ?record= the page sends the reader to the remembered or the landing record, as its own address");
  check(/LAST_RECORD_COOKIE = "mgda-context-last"/u.test(page) && /Max-Age=\$\{LAST_RECORD_SECONDS\}/u.test(readFileSync(join(route, "desktop/ContextDesktop.tsx"), "utf8")) && /LAST_RECORD_SECONDS = 30 \* 60/u.test(readFileSync(join(route, "desktop/ContextDesktop.tsx"), "utf8")), "the remembered object lives in a thirty-minute first-party cookie");
  /* the landing record: reader-facing, all three dimensions, the most context any object carries */
  const landing = getGovernedContextLandingRecord();
  const landingLookup = lookupGovernedContextDataset(landing.stableId);
  check(landingLookup.ok === true, "the landing record loads");
  const landingReps = landingLookup.data.representations;
  check(new Set(landingReps.map((r) => r.kind)).size === 3 && landingReps.length === 4, "the landing record carries all three dimensions and four contexts");
  check(getGovernedContextExampleOptions().some((e) => e.stableId === landing.stableId), "the landing record is among the examples");
  check(page.indexOf("isLikelyMobileTraceRequest()") < page.indexOf("await Promise.all"), "the mobile guard precedes the runtime imports");
}

for (const real of REAL) {
  const lookup = lookupGovernedContextDataset(real.id);
  check(lookup.ok, `${real.id} resolves`);
  const described = describe(lookup.data);
  checkConnectionContract(described);
  checkLayouts(described, real.nodes);
  checkCard(described, real.id);
  checkClipboard(described, real.id);
}

/* the synthetic stress fixture, a defensive layout test only */
const base = lookupGovernedContextDataset(defaultId).data;
for (const variant of ["full", "missing"]) {
  const fixture = stress.buildStressFixture(base, variant);
  check(fixture.selectedRecord.surfaceId === stress.STRESS_STABLE_ID, `stress/${variant}: its own id`);
  check(fixture.representations.length === (variant === "full" ? 13 : 10), `stress/${variant}: 4 / 6 / ${variant === "full" ? 3 : 0} terms`);
  const described = describe(fixture);
  checkConnectionContract(described);
  checkLayouts(described, variant === "full" ? 14 : 11);
  checkCard(described, `stress/${variant}`);
  checkClipboard(described, `stress/${variant}`);
}

console.log(`CONTEXT_CANVAS_DESIGN=PASS CHECKS=${checks} REAL_OBJECTS=${REAL.length} LAYOUTS=${PRESETS.length}`);
