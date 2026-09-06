import type { Catalogue } from "./catalogue";
import { defaultState, PAGE, type FilterState } from "./filter";

// Entry-scoped state preserves the reader's place on Object -> Back without
// replacing Next's own history keys or persisting a different release's data.
export function restoreDirectory(catalogue: Catalogue): { state: FilterState; shown: number } {
  const saved = window.history.state?.mgdaDirectory;
  const state = saved?.state;
  if (saved?.version === 1 && saved.releaseId === catalogue.releaseId && state
    && (state.place === null || catalogue.places.includes(state.place))
    && Number.isInteger(state.yearFrom) && Number.isInteger(state.yearTo)
    && state.yearFrom >= catalogue.yearMin && state.yearTo <= catalogue.yearMax && state.yearFrom <= state.yearTo
    && Array.isArray(state.themes) && state.themes.every((theme: unknown) => typeof theme === "string" && catalogue.themes.includes(theme))
    && ["all", "source", "remote", "citation"].includes(state.visual) && ["oldest", "newest"].includes(state.order)
    && Number.isInteger(saved.shown) && saved.shown >= PAGE && saved.shown <= catalogue.count + PAGE) {
    return { state, shown: saved.shown };
  }
  return { state: defaultState(catalogue), shown: PAGE };
}

export function rememberDirectory(releaseId: string, state: FilterState, shown: number) {
  window.history.replaceState({ ...window.history.state, mgdaDirectory: { version: 1, releaseId, state, shown } }, "");
}
