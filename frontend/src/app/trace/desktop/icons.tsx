/* The three function glyphs, by the nav's control rule (the same 60 px
   box, the same 2 px border) but drawn larger and lighter, as the owner
   asked: 38 px, a 1.8 stroke with round caps on a 24-unit grid, each
   mark's bounding box centred on (12,12) (measured in the browser).
   Context Canvas: connect — one node joined to two; Spacetime: a compass
   (preferred to a map pin); Exploration: an open eye that shines. */

const common = {
  width: 38,
  height: 38,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

/* Context Canvas — connect: one node joined to two */
export function ContextGlyph() {
  return (
    <svg {...common}>
      <circle cx="5.5" cy="12" r="3" />
      <circle cx="18.5" cy="5.5" r="3" />
      <circle cx="18.5" cy="18.5" r="3" />
      <path d="M8.5 12h3.5l4.2-4.4M12 12l4.2 4.4" />
    </svg>
  );
}

/* Spacetime — a compass */
export function SpacetimeGlyph() {
  return (
    <svg {...common}>
      <circle cx="12" cy="12" r="9.5" />
      <path d="M7.6 16.4l2.6-6.2 6.2-2.6-2.6 6.2z" fill="currentColor" strokeLinejoin="round" />
      <circle cx="12" cy="12" r="1.3" fill="#050506" stroke="none" />
    </svg>
  );
}

/* Exploration — an open eye that shines: the eye on the box's centre,
   its rays all round it, so the mark sits dead centre */
export function ExplorationGlyph() {
  return (
    <svg {...common}>
      <path d="M5.2 12c2-3.2 4.3-4.8 6.8-4.8s4.8 1.6 6.8 4.8c-2 3.2-4.3 4.8-6.8 4.8S7.2 15.2 5.2 12z" />
      <circle cx="12" cy="12" r="2.1" fill="currentColor" stroke="none" />
      <path d="M12 1.6v2.6M12 19.8v2.6M1.6 12h2.6M19.8 12h2.6M4.65 4.65l1.85 1.85M17.5 17.5l1.85 1.85M4.65 19.35l1.85-1.85M17.5 6.5l1.85-1.85" strokeWidth="1.5" />
    </svg>
  );
}
