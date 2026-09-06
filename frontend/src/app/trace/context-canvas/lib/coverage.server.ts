import "server-only";

/* How many public records each governed term is assigned to, read from
   the projection's own term registry (generated/trace-context-v1/
   terms.json — the file the governed reader has already verified against
   the manifest before any dataset is served). A count, shown in the
   inspector beside the term; not a relation between records, not a
   weight, and never a criterion for anything on the canvas. */

import termsJson from "../../../../../generated/trace-context-v1/terms.json";

type TermRegistry = Readonly<{
  terms: readonly Readonly<{ id: string; assignmentCount: number }>[];
}>;

export function coverageForTermIds(
  termIds: readonly string[],
): Readonly<Record<string, number>> {
  const byId = new Map(
    (termsJson as unknown as TermRegistry).terms.map((term) => [term.id, term.assignmentCount] as const),
  );
  return Object.freeze(Object.fromEntries(
    termIds.flatMap((id) => {
      const count = byId.get(id);
      return Number.isSafeInteger(count) && (count as number) >= 0 ? [[id, count as number]] : [];
    }),
  ));
}
