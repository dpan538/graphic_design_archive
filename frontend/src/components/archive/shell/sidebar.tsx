import { getGlobalCounts } from "@/lib/archive-data";

/** Compact archive-counts card (shown fixed at the bottom-right). */
export function CountsCard() {
  const c = getGlobalCounts();
  const rows: Array<[string, number]> = [
    ["folders", c.folders],
    ["surfaces", c.surfaces],
    ["sheets", c.sheets],
    ["cards", c.cards],
    ["stubs", c.stubs],
    ["sources", c.sources],
  ];
  return (
    <div className="text-[0.74rem]">
      <div className="label-caps border-b-[1.5px] border-ink pb-1.5 mb-2">
        Archive counts
      </div>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-1.5">
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-baseline justify-between gap-3">
            <dt className="text-ink-soft uppercase tracking-wide text-[0.6rem]">
              {k}
            </dt>
            <dd className="font-bold text-base tabular-nums">{v}</dd>
          </div>
        ))}
      </dl>
      <div className="mt-2 pt-2 border-t border-line-soft flex items-baseline justify-between gap-3">
        <span className="text-ink-soft uppercase tracking-wide text-[0.6rem]">
          images
        </span>
        <span className="font-bold text-base tabular-nums">
          {c.imageCoveragePercent}%
        </span>
      </div>
      <div className="mt-1 text-[0.52rem] uppercase tracking-[0.1em] text-ink-soft">
        target 90% · {c.imageCoverageHealthy ? "healthy" : "needs source expansion"}
      </div>
    </div>
  );
}
