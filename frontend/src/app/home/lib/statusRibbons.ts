/* Plate 1 of 04 · Research Status — the mirrored ranked stream.

   Two references fused (HOMEPAGE_DESIGN_v1.md §6): the ranked, crossing
   ribbons of the UK-cities population chart, and the white spectrogram poster
   whose bands mirror about a horizontal axis. Above the axis: every PUBLIC
   record by place. Below it: every HELD record by place. One ribbon is one
   place; its thickness is records per five years; its colour is rank by
   total. The asymmetry of the release is the composition itself — no zero
   has to be printed for it to be seen.

   Everything here is computed once, on the server, from the frozen v49
   per-record dataset. Coordinates are rounded so SSR and client agree. */
import { STATUS } from "./statusLayout";

export const RB_Y0 = 1900;
export const RB_Y1 = 2026;
export const RB_NB = 26; // five-year bins, 1900–04 … 2025–26
export const RB_AXIS_YEARS = [1900, 1925, 1950, 1975, 2000, 2025];
export const VW = 1000;
export const HALF = 500;
export const VH = HALF * 2;
/* Ribbons per half — named places, region groups, and one residual. */
export const RIBBONS = 15;
const GROUP_MIN = 150;
const GROUP_PLACES = 5;
/* Records per five years that fill one half. 1965–69 (1,212 public) and
   1985–89 (1,037) overrun the sheet the way the last column of the
   spectrogram poster does — the first caption after the draw says why. */
export const SCALE_RECORDS = 1000;
export const UNIT = HALF / SCALE_RECORDS;
export const TICKS = [250, 500, 750, 1000];
/* column width of the build's bars; bins are 40 units apart */
export const RB_BW = 30;
/* Minimum label pitch in viewBox units. The chart fills its box (the SVG is
   stretched, not fitted), so at the designed 740px height 32 units is 24px —
   14px labels with air, 30 of them. */
const LABEL_PITCH = 32;

export type Ribbon = {
  key: string;
  place: string;
  label: string;
  total: number;
  counts: number[];
  rank: number;
  color: string;
  text: string;
  /* number of places folded into this ribbon; undefined for a named place */
  places?: number;
  path: string;
  /* centre y (viewBox units) at the first and last bin */
  y0: number;
  y1: number;
  /* the ribbon as 26 columns, [top, bottom] in viewBox units — the bars the
     build raises one bin at a time before the smooth band develops */
  cols: [number, number][];
};
export type LabelSlot = { rb: Ribbon; y: number; anchor: number; side: 0 | 1 };
export type Half = {
  kind: "public" | "held";
  total: number;
  ribbons: Ribbon[];
  binTotals: number[];
};

const r1 = (n: number) => Math.round(n * 10) / 10;
const X = (b: number) => r1((b * VW) / (RB_NB - 1));

/* ---- colour: the cities chart's rank rainbow, red at the axis → purple at
   the edge. Text gets the same hue pulled toward ink for contrast on white. */
/* A spectral ramp rather than the cities chart's print inks. Read from the
   axis outward: the spectrogram poster keeps its largest series blue at the
   centre and lets the warm colours fringe it, so rank 0 is blue here and the
   smallest ribbons run through yellow and red to magenta. */
const STOPS = ["#2b6cff", "#22b4c8", "#8fd83a", "#f5df2a", "#ffb300", "#ff7a1f", "#ff3d2e", "#ff2e7a", "#c02bd6", "#7a3dff", "#4f5cff"];
function hex(c: string) {
  return [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
}
function toHex(rgb: number[]) {
  return "#" + rgb.map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, "0")).join("");
}
function mix(a: number[], b: number[], t: number) {
  return a.map((v, i) => v + (b[i] - v) * t);
}
export function rankColor(rank: number, count: number) {
  const t = count <= 1 ? 0 : rank / (count - 1);
  const f = t * (STOPS.length - 1);
  const i = Math.min(Math.floor(f), STOPS.length - 2);
  return toHex(mix(hex(STOPS[i]), hex(STOPS[i + 1]), f - i));
}
const INK = hex("#1c1a16");
export function textColor(color: string) {
  return toHex(mix(hex(color), INK, 0.36));
}

/* ---- labels: the last path segment, unless that collides ---- */
const ABBR: Record<string, string> = {
  "Southeast Asia": "SE Asia",
  "Middle East and North Africa": "MENA",
  "Eastern Europe": "E. Europe",
  "Latin America": "Latin America",
};
const abbr = (s: string) => ABBR[s] ?? s;
function shortLabel(place: string, collide: Set<string>) {
  const parts = place.split(" / ");
  const last = parts[parts.length - 1];
  if (last[0] === last[0].toLowerCase()) return place; // "Global / transnational"
  if (!collide.has(last) || parts.length < 2) return last;
  return `${last} (${abbr(parts[parts.length - 2])})`;
}
/* The same rule for any list of places: short where unambiguous within the
   list, parent-qualified where two places share a last segment. */
export function shortNames(places: string[]): string[] {
  const seen = new Map<string, Set<string>>();
  for (const p of places) {
    const last = p.split(" / ").pop()!;
    if (!seen.has(last)) seen.set(last, new Set());
    seen.get(last)!.add(p);
  }
  const collide = new Set([...seen.entries()].filter(([, s]) => s.size > 1).map(([k]) => k));
  return places.map((p) => shortLabel(p, collide));
}

/* ---- the two halves ---- */
function buildHalf(kind: "public" | "held"): Half {
  const per = new Map<number, number[]>();
  for (const o of STATUS.objects) {
    const y = o[0];
    if (y < RB_Y0 || y > RB_Y1) continue;
    if ((o[2] === 0) !== (kind === "public")) continue;
    const b = Math.min(Math.floor((y - RB_Y0) / 5), RB_NB - 1);
    let row = per.get(o[1]);
    if (!row) {
      row = new Array<number>(RB_NB).fill(0);
      per.set(o[1], row);
    }
    row[b] += 1;
  }
  const rows = [...per.entries()]
    .map(([p, counts]) => ({ p, counts, total: counts.reduce((a, c) => a + c, 0) }))
    .sort((a, b) => b.total - a.total || a.p - b.p);
  /* The residual is not one anonymous band. Where a region prefix gathers
     enough of it (GROUP_MIN records across GROUP_PLACES places) it becomes
     its own ribbon — "Latin America · 31 other places" — and only what is
     left folds into "Other countries". Named ribbons give way to groups so
     that a half never exceeds RIBBONS labels. */
  const regionOf = (p: number) => {
    const parts = STATUS.ledger[p].place.split(" / ");
    return parts.length > 1 ? parts[0] : "";
  };
  let named = rows.slice(0, RIBBONS - 1);
  let groups: { region: string; counts: number[]; total: number; places: number }[] = [];
  for (let pass = 0; pass < 4; pass++) {
    const rest = rows.slice(named.length);
    const byRegion = new Map<string, { counts: number[]; total: number; places: number }>();
    for (const r of rest) {
      const key = regionOf(r.p);
      if (!key) continue;
      const g = byRegion.get(key) ?? { counts: new Array<number>(RB_NB).fill(0), total: 0, places: 0 };
      r.counts.forEach((c, i) => (g.counts[i] += c));
      g.total += r.total;
      g.places += 1;
      byRegion.set(key, g);
    }
    const next = [...byRegion.entries()]
      .filter(([, g]) => g.total >= GROUP_MIN && g.places >= GROUP_PLACES)
      .map(([region, g]) => ({ region, ...g }))
      .sort((a, b) => b.total - a.total);
    const want = RIBBONS - 1 - next.length;
    groups = next;
    if (want === named.length) break;
    named = rows.slice(0, want);
  }
  const grouped = new Set(groups.map((g) => g.region));
  const rest = rows.slice(named.length).filter((r) => !grouped.has(regionOf(r.p)));
  const other = new Array<number>(RB_NB).fill(0);
  for (const r of rest) r.counts.forEach((c, i) => (other[i] += c));
  const otherTotal = other.reduce((a, c) => a + c, 0);

  const seed: Omit<Ribbon, "rank" | "color" | "text" | "path" | "y0" | "y1" | "label" | "cols">[] = named.map((r) => ({
    key: `${kind}-${r.p}`,
    place: STATUS.ledger[r.p].place,
    total: r.total,
    counts: r.counts,
  }));
  for (const g of groups) {
    seed.push({
      key: `${kind}-group-${g.region}`,
      place: `${abbr(g.region)} +${g.places} places`,
      total: g.total,
      counts: g.counts,
      places: g.places,
    });
  }
  seed.push({
    key: `${kind}-other`,
    place: `${rest.length} more countries`,
    total: otherTotal,
    counts: other,
    places: rest.length,
  });
  /* Rank by total — this fixes colour and the stacking tie-break. */
  const byTotal = [...seed].sort((a, b) => b.total - a.total);
  const rankOf = new Map(byTotal.map((s, i) => [s.key, i]));

  /* Stacking order per bin: by activity over the trailing fifteen years, so
     the places being gathered in an era rise to the axis and the ribbons
     cross when eras change — the cities chart's braid, but with meaning. */
  const n = seed.length;
  const order: number[][] = [];
  for (let b = 0; b < RB_NB; b++) {
    const act = seed.map((s, i) => ({
      i,
      a: s.counts[b] + (s.counts[b - 1] ?? 0) + (s.counts[b - 2] ?? 0),
      r: rankOf.get(s.key)!,
    }));
    act.sort((p, q) => q.a - p.a || p.r - q.r);
    order.push(act.map((a) => a.i));
  }
  /* y extents (record units from the axis) per ribbon per bin. */
  const lo: number[][] = seed.map(() => new Array<number>(RB_NB).fill(0));
  const hi: number[][] = seed.map(() => new Array<number>(RB_NB).fill(0));
  for (let b = 0; b < RB_NB; b++) {
    let y = 0;
    for (const i of order[b]) {
      lo[i][b] = y;
      y += seed[i].counts[b] * UNIT;
      hi[i][b] = y;
    }
  }
  const sign = kind === "public" ? -1 : 1;
  const Y = (units: number) => r1(HALF + sign * units);

  const ribbons: Ribbon[] = seed.map((s, i) => {
    /* outer boundary forward, inner boundary back; eased steps between bins */
    const outer = hi[i].map((u, b) => [X(b), Y(u)]);
    const inner = lo[i].map((u, b) => [X(b), Y(u)]);
    let d = `M${outer[0][0]},${outer[0][1]}`;
    for (let b = 1; b < RB_NB; b++) {
      const [x0, y0] = outer[b - 1];
      const [x1, y1] = outer[b];
      const cx = r1((x0 + x1) / 2);
      d += `C${cx},${y0} ${cx},${y1} ${x1},${y1}`;
    }
    d += `L${inner[RB_NB - 1][0]},${inner[RB_NB - 1][1]}`;
    for (let b = RB_NB - 2; b >= 0; b--) {
      const [x0, y0] = inner[b + 1];
      const [x1, y1] = inner[b];
      const cx = r1((x0 + x1) / 2);
      d += `C${cx},${y0} ${cx},${y1} ${x1},${y1}`;
    }
    d += "Z";
    const rank = rankOf.get(s.key)!;
    const color = rankColor(rank, n);
    const cols = outer.map((o, b) => {
      const a = o[1];
      const c = inner[b][1];
      return [Math.min(a, c), Math.max(a, c)] as [number, number];
    });
    return {
      ...s,
      label: s.place,
      rank,
      color,
      text: textColor(color),
      path: d,
      y0: r1((outer[0][1] + inner[0][1]) / 2),
      y1: r1((outer[RB_NB - 1][1] + inner[RB_NB - 1][1]) / 2),
      cols,
    };
  });
  const binTotals = new Array<number>(RB_NB).fill(0);
  for (const s of seed) s.counts.forEach((c, b) => (binTotals[b] += c));
  return { kind, total: seed.reduce((a, s) => a + s.total, 0), ribbons, binTotals };
}

export const PUBLIC = buildHalf("public");
export const HELD = buildHalf("held");

/* Short labels, disambiguated across both halves. */
{
  const all = [...PUBLIC.ribbons, ...HELD.ribbons].filter((r) => !r.places);
  const seen = new Map<string, Set<string>>();
  for (const r of all) {
    const last = r.place.split(" / ").pop()!;
    if (!seen.has(last)) seen.set(last, new Set());
    seen.get(last)!.add(r.place);
  }
  const collide = new Set([...seen.entries()].filter(([, s]) => s.size > 1).map(([k]) => k));
  for (const r of all) r.label = shortLabel(r.place, collide);
  for (const r of [...PUBLIC.ribbons, ...HELD.ribbons]) if (r.places) r.label = r.place;
}

/* ---- label columns: greedy pitch, both halves share a side ---- */
function layoutSide(side: 0 | 1): LabelSlot[] {
  const slots: LabelSlot[] = [...PUBLIC.ribbons, ...HELD.ribbons].map((rb) => ({
    rb,
    anchor: side === 0 ? rb.y0 : rb.y1,
    y: side === 0 ? rb.y0 : rb.y1,
    side,
  }));
  slots.sort((a, b) => a.anchor - b.anchor || a.rb.rank - b.rb.rank);
  /* push down, then pull the tail back inside the sheet, then re-space */
  for (let i = 1; i < slots.length; i++) {
    slots[i].y = Math.max(slots[i].y, slots[i - 1].y + LABEL_PITCH);
  }
  const over = slots[slots.length - 1].y - (VH - LABEL_PITCH / 2);
  if (over > 0) {
    for (let i = slots.length - 1; i >= 0; i--) {
      const want = slots[i].y - over;
      slots[i].y = i === slots.length - 1 ? want : Math.min(slots[i].y, slots[i + 1].y - LABEL_PITCH);
    }
  }
  for (const s of slots) s.y = r1(Math.max(LABEL_PITCH / 2, s.y));
  return slots;
}
/* Only the 2026 end is named. The 1900 end was tried: every ribbon starts
   near the axis there, so 34 leaders fanned out of one point and the column
   read as clutter, not as the cities chart's list. */
export const LABELS_R = layoutSide(1);

/* One colour per place across both halves (public first), so the tables in
   the margin can carry the ribbon's hue and read as the same figure. */
export const PLACE_COLOR = new Map<string, string>();
for (const r of [...PUBLIC.ribbons, ...HELD.ribbons]) {
  if (!r.places && !PLACE_COLOR.has(r.place)) PLACE_COLOR.set(r.place, r.color);
}

/* ---- figures the captions quote — all from the data above ---- */
const fmt = (n: number) => n.toLocaleString("en-GB");
export const IN_RANGE = PUBLIC.total + HELD.total;
export const BEFORE_1900 = STATUS.objects.filter((o) => o[0] >= 0 && o[0] < RB_Y0).length;
const peakBin = PUBLIC.binTotals
  .map((p, b) => ({ b, t: p + HELD.binTotals[b] }))
  .sort((a, b) => b.t - a.t)[0];
const yearCounts = new Map<number, number>();
for (const o of STATUS.objects) yearCounts.set(o[0], (yearCounts.get(o[0]) ?? 0) + 1);
const peakYear = [...yearCounts.entries()].sort((a, b) => b[1] - a[1])[0];
export const PEAK = {
  binStart: RB_Y0 + peakBin.b * 5,
  binEnd: RB_Y0 + peakBin.b * 5 + 4,
  binTotal: peakBin.t,
  year: peakYear[0],
  yearTotal: peakYear[1],
};
const topN = (h: Half, n: number) =>
  h.ribbons
    .filter((r) => !r.places)
    .slice(0, n)
    .map((r) => `${r.label} ${fmt(r.total)}`)
    .join(" · ");
const heldFull = HELD.ribbons
  .filter((r) => !r.places)
  .slice(0, 5)
  .filter((r) => STATUS.ledger.find((l) => l.place === r.place)!.public === 0).length;

/* Where the lens goes after the sheet is drawn. `at` is in viewport-heights
   of scroll from the top of the section; px/py are fractions of the chart
   row (labels + sheet); k is magnification. */
export type Lens = { at: number; k: number; px: number; py: number; id: string; caption: string };
export const DRAW_VH = 2;
export const LENSES: Lens[] = [
  {
    at: 2.0, k: 2.0, px: 0.4, py: 0.5, id: `${PEAK.binStart}–${String(PEAK.binEnd).slice(2)}`,
    caption: `${PEAK.binStart}–${PEAK.binEnd}: ${fmt(PEAK.binTotal)} records in five years, ${fmt(PEAK.yearTotal)} of them dated ${PEAK.year} — one bulk capture, and the widest band on the sheet. It is a fact about gathering, not about the year.`,
  },
  {
    at: 2.65, k: 1.6, px: 0.76, py: 0.31, id: "public",
    caption: `Public, ranked by records 1900–2026: ${topN(PUBLIC, 5)}. Where the archive's sources are, the archive is published.`,
  },
  {
    at: 3.3, k: 1.6, px: 0.76, py: 0.71, id: "held",
    caption: `Held, ranked the same way: ${topN(HELD, 5)}. ${heldFull === 5 ? "All five" : `${heldFull} of the five`} are held in full — every record keeps its year, place and source, and waits on evidence and rights, not on rediscovery.`,
  },
];
export const DRAW_CAPTION = `Above the line, public records by place — ${fmt(PUBLIC.total)}. Below it, held — ${fmt(HELD.total)}. One ribbon is one place; thickness is records per five years; colour is rank by total. ${fmt(BEFORE_1900)} records dated before 1900 are on the panorama that follows.`;
