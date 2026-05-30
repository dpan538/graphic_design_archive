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
    </div>
  );
}
