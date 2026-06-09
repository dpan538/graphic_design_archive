import type { FolderTypeKey, ImageState, SurfaceKind } from "@/types/archive";
import { getFolderInk } from "@/lib/archive-data";

/** Small shared building blocks, kept quiet and typographic (no chrome boxes). */

export function ImgBadge({ state }: { state: ImageState }) {
  return (
    <span
      className="text-ink-soft tabular-nums"
      style={{ fontSize: "0.56rem", letterSpacing: "0.08em" }}
      title={`Image state ${state}`}
    >
      {state}
    </span>
  );
}

const KIND_LABEL: Record<SurfaceKind, string> = {
  sheet: "Sheet",
  card: "Card",
  fallback_stub: "Stub",
};

export function StatusChip({ kind }: { kind: SurfaceKind }) {
  return (
    <span
      className={`label-caps ${kind === "fallback_stub" ? "text-medium-readable" : "text-ink-soft"}`}
    >
      {KIND_LABEL[kind]}
    </span>
  );
}

export function TypeSwatch({ type }: { type: FolderTypeKey }) {
  return (
    <span
      aria-hidden
      className="inline-block w-2.5 h-2.5 border border-ink align-middle"
      style={{ backgroundColor: getFolderInk(type) }}
    />
  );
}

/** Inline type label paired with a colour swatch (colour never alone). */
export function TypeLabel({ type }: { type: FolderTypeKey }) {
  return (
    <span className="inline-flex items-center gap-1.5 label-caps">
      <TypeSwatch type={type} />
      {type}
    </span>
  );
}

/** Small-caps field label used above values. */
export function Kicker({ children }: { children: React.ReactNode }) {
  return <span className="label-caps text-ink-soft">{children}</span>;
}
