"use client";

import { useEffect, useMemo, useState } from "react";
import YearInput from "@/components/site/YearInput";
import { X } from "lucide-react";
import { themeInk } from "../lib/palette";
import { decadesFor, erasFor, VISUAL_OPTIONS, type FilterState, type Order } from "../lib/filter";
import type { CatalogueBounds } from "../lib/catalogue";
import styles from "./IndexFilterDrawer.module.css";

/* The filter set lives in a drawer, opened deliberately from the control bar.
   One spacing rhythm throughout: --s-6 between sections, --s-3 within. */
export default function IndexFilterDrawer({
  open,
  state,
  patch,
  count,
  total,
  bounds,
  places,
  themes,
  onClose,
}: {
  open: boolean;
  state: FilterState;
  patch: (p: Partial<FilterState>) => void;
  count: number;
  total: number;
  bounds: CatalogueBounds;
  places: string[];
  themes: string[];
  onClose: () => void;
}) {
  const DECADES = decadesFor(bounds);
  const ERAS = erasFor(bounds);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const eraActive = ERAS.find(
    ([, a, b]) => state.yearFrom === a && state.yearTo === b,
  );
  const decadeActive =
    state.yearTo - state.yearFrom === 9 && state.yearFrom % 10 === 0
      ? state.yearFrom
      : null;

  return (
    <div className={styles.overlay}>
      <button
        type="button"
        className={styles.scrim}
        aria-label="Close filters"
        onClick={onClose}
      />
      <div className={styles.drawer} role="dialog" aria-label="Filter the directory">
        <div className={styles.head}>
          <div>
            <span className={styles.title}>Filter</span>
            <p className={styles.headCount}>
              {count.toLocaleString()} of {total.toLocaleString()} records match
            </p>
          </div>
          <button type="button" className={styles.close} onClick={onClose} aria-label="Close">
            <X size={20} strokeWidth={3} aria-hidden="true" />
          </button>
        </div>

        <div className={styles.body}>
          <Region value={state.place} places={places} onPick={(place) => patch({ place })} />

          <section className={styles.group}>
            <span className={styles.label}>Year</span>
            <div className={styles.field}>
              <div className={styles.yearRange}>
                <YearInput
                  className={styles.yearInput}
                  type="number"
                  inputMode="numeric"
                  aria-label="From year"
                  value={state.yearFrom}
                  min={bounds.yearMin} max={state.yearTo}
                  onCommit={(value) => patch({ yearFrom: value ?? bounds.yearMin })}
                />
                <span className={styles.dash} aria-hidden="true">
                  —
                </span>
                <YearInput
                  className={styles.yearInput}
                  type="number"
                  inputMode="numeric"
                  aria-label="To year"
                  value={state.yearTo}
                  min={state.yearFrom} max={bounds.yearMax}
                  onCommit={(value) => patch({ yearTo: value ?? bounds.yearMax })}
                />
              </div>
            </div>
            <div className={styles.field}>
              <div className={styles.eras}>
                {ERAS.map(([l, a, b]) => (
                  <button
                    key={l}
                    type="button"
                    className={styles.era}
                    data-on={eraActive?.[0] === l || undefined}
                    onClick={() =>
                      eraActive?.[0] === l
                        ? patch({ yearFrom: bounds.yearMin, yearTo: bounds.yearMax })
                        : patch({ yearFrom: a, yearTo: b })
                    }
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>
            <div className={styles.field}>
              <div className={styles.decades}>
                {DECADES.map((d) => (
                  <button
                    key={d}
                    type="button"
                    className={styles.decade}
                    data-on={decadeActive === d || undefined}
                    onClick={() =>
                      decadeActive === d
                        ? patch({ yearFrom: bounds.yearMin, yearTo: bounds.yearMax })
                        : patch({
                            yearFrom: Math.max(bounds.yearMin, d),
                            yearTo: Math.min(bounds.yearMax, d + 9),
                          })
                    }
                  >
                    {`${String(d).slice(2)}s`}
                  </button>
                ))}
              </div>
            </div>
          </section>

          <section className={styles.group}>
            <span className={styles.label}>Order</span>
            <div className={styles.field}>
              <div className={styles.order}>
                {(
                  [
                    ["oldest", "Oldest first"],
                    ["newest", "Newest first"],
                  ] as [Order, string][]
                ).map(([v, l]) => (
                  <button
                    key={v}
                    type="button"
                    className={styles.orderBtn}
                    data-on={state.order === v || undefined}
                    aria-pressed={state.order === v}
                    onClick={() => patch({ order: v })}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* visual access — interim labels (FRONTEND_DESIGN_DECISION.md §3c):
              "remote visual candidate" is not "has image"; nothing is
              displayable until the visual registry says so */}
          <section className={styles.group}>
            <span className={styles.label}>Visual access</span>
            <div className={styles.field}>
              <div className={styles.badges}>
                {VISUAL_OPTIONS.map(([v, l]) => (
                  <button
                    key={v}
                    type="button"
                    className={styles.badge}
                    data-on={state.visual === v || undefined}
                    aria-pressed={state.visual === v}
                    onClick={() => patch({ visual: v })}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>
          </section>

          <section className={styles.group}>
            <span className={styles.label} data-accent="green">
              Theme
            </span>
            <div className={styles.field}>
              <div className={styles.badges}>
                <button
                  type="button"
                  className={styles.badge}
                  data-on={state.themes.length === 0 || undefined}
                  onClick={() => patch({ themes: [] })}
                >
                  All
                </button>
                {themes.map((t) => {
                  const on = state.themes.includes(t);
                  return (
                    <button
                      key={t}
                      type="button"
                      className={styles.badge}
                      data-on={on || undefined}
                      aria-pressed={on}
                      style={on ? { background: themeInk(t), borderColor: themeInk(t) } : undefined}
                      onClick={() =>
                        patch({
                          themes: on
                            ? state.themes.filter((x) => x !== t)
                            : [...state.themes, t],
                        })
                      }
                    >
                      {t}
                    </button>
                  );
                })}
              </div>
            </div>
          </section>
        </div>

        <button type="button" className={styles.apply} onClick={onClose}>
          Show {String(count).padStart(3, "0")} {count === 1 ? "object" : "objects"}
        </button>
      </div>
    </div>
  );
}

function Region({
  value,
  places,
  onPick,
}: {
  value: string | null;
  places: string[];
  onPick: (r: string | null) => void;
}) {
  const [q, setQ] = useState("");
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return needle ? places.filter((r) => r.toLowerCase().includes(needle)) : places;
  }, [q, places]);

  return (
    <section className={styles.group}>
      <span className={styles.label} data-accent="blue">
        Place (as recorded)
      </span>
      <div className={styles.field}>
        <input
          className={styles.search}
          type="text"
          placeholder="Filter places…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <div className={styles.field}>
        <ul className={styles.regionList} role="list">
          <li>
            <button
              type="button"
              className={styles.regionItem}
              data-on={value === null || undefined}
              onClick={() => onPick(null)}
            >
              All places
            </button>
          </li>
          {shown.map((r) => (
            <li key={r}>
              <button
                type="button"
                className={styles.regionItem}
                data-on={value === r || undefined}
                onClick={() => onPick(r)}
              >
                {r}
              </button>
            </li>
          ))}
          {shown.length === 0 ? (
            <li className={styles.regionNone}>No place matches “{q}”.</li>
          ) : null}
        </ul>
      </div>
    </section>
  );
}
