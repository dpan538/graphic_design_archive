/** Internal-only deterministic SVG renderer for Python-authored Round 15 images. */

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new TypeError("object required");
  return value as Record<string, unknown>;
}
function escape(value: unknown): string {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character] ?? character);
}

export function renderRound15ResearchSvg(value: unknown): string {
  const image = record(value);
  const semantic = record(image.semantic_core);
  const composition = record(image.composition_core);
  const hints = record(image.presentation_hints);
  if (!Array.isArray(hints.node_positions) || !Array.isArray(hints.edge_hints)) throw new TypeError("presentation hints required");
  const positions = new Map(hints.node_positions.map((raw) => {
    const node = record(raw);
    return [String(node.node_id), node];
  }));
  const gaps = new Set(Array.isArray(semantic.evidence_gap_node_ids) ? semantic.evidence_gap_node_ids.map(String) : []);
  const edgeSvg = hints.edge_hints.map((raw) => {
    const edge = record(raw);
    const source = positions.get(String(edge.source_node_id));
    const target = positions.get(String(edge.target_node_id));
    if (!source || !target) throw new TypeError("edge endpoint missing");
    return `<g data-association-id="${escape(edge.association_id)}" data-support-class="${escape(edge.support_class_label)}"><line x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}" stroke="#4d5964" stroke-width="2"/><title>Qualified generic association; ${escape(edge.support_class_label)}. No direction or typed relation.</title></g>`;
  }).join("");
  const nodeSvg = hints.node_positions.map((raw) => {
    const node = record(raw);
    const gap = gaps.has(String(node.node_id));
    return `<g data-node-id="${escape(node.node_id)}" data-layout-role="${escape(node.layout_role)}"><circle cx="${node.x}" cy="${node.y}" r="16" fill="${gap ? "#fffaf0" : "#f7f4ec"}" stroke="#27313a" stroke-width="1.5"${gap ? ' stroke-dasharray="4 3"' : ""}/><text x="${node.x}" y="${Number(node.y) + 29}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" fill="#27313a">${escape(node.node_id)}</text>${gap ? `<text x="${node.x}" y="${Number(node.y) + 43}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="9" fill="#7b5e2b">unresolved evidence</text>` : ""}</g>`;
  }).join("");
  const candidates = Array.isArray(composition.candidate_decisions) ? composition.candidate_decisions.map(record) : [];
  const boundedNotes = candidates.filter((item) => ["PRUNED", "UNRESOLVED"].includes(String(item.decision_state))).slice(0, 3)
    .map((item, index) => `<text x="24" y="${470 + index * 16}" font-family="system-ui,sans-serif" font-size="10" fill="#5b6268">${escape(item.decision_state)} · ${escape(item.assessment_id)} · composition decision, not historical rejection</text>`).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="720" height="540" viewBox="0 0 720 540" role="img" aria-labelledby="title desc" data-internal-research-only="true"><title id="title">${escape(semantic.semantic_image_id)} internal composition research view</title><desc id="desc">Undirected generic associations with equal-size nodes and equal-width lines. Geometry, split, pruning, and gaps are not historical facts.</desc><rect width="720" height="540" fill="#fffdf8"/><text x="24" y="26" font-family="system-ui,sans-serif" font-size="14" font-weight="600" fill="#27313a">${escape(semantic.topology_type)} · internal research only</text><text x="24" y="44" font-family="system-ui,sans-serif" font-size="10" fill="#5b6268">Equal node size · equal line width · no arrowheads · circular placement is cosmetic</text>${edgeSvg}${nodeSvg}${boundedNotes}<text x="696" y="522" text-anchor="end" font-family="system-ui,sans-serif" font-size="9" fill="#737a80">association ≠ typed historical relation</text></svg>`;
}
