"use client";

import YearInput from "@/components/site/YearInput";

import { useEffect, useState, type ReactNode } from "react";
import { ChevronDown, X } from "lucide-react";
import { themeInk } from "../lib/palette";
import { decadesFor, erasFor, summarize, VISUAL_OPTIONS, type FilterState, type Order } from "../lib/filter";
import type { CatalogueBounds } from "../lib/catalogue";
import styles from "./IndexMobileFilters.module.css";

type SectionKey = "region" | "year" | "order" | "theme" | "visual";

/* Bottom sheet — sections are an accordion, all collapsed on open, so the sheet
   is short. Each header shows its current value. */
export default function IndexMobileSheet({
  open,
  state,
  patch,
  count,
  bounds,
  places,
  themes,
  onClose,
}: {
  open: boolean;
  state: FilterState;
  patch: (p: Partial<FilterState>) => void;
  count: number;
  bounds: CatalogueBounds;
  places: string[];
  themes: string[];
  onClose: () => void;
}) {
  const [openKey, setOpenKey] = useState<SectionKey | null>(null);
  const DECADES = decadesFor(bounds);
  const ERAS = erasFor(bounds);

  useEffect(() => {
    if (!open) return;
    setOpenKey(null);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const sum = summarize(state, bounds);
  const toggle = (k: SectionKey) => setOpenKey((cur) => (cur === k ? null : k));

  const eraActive = ERAS.find(([, a, b]) => state.yearFrom === a && state.yearTo === b);
  const decadeActive =
    state.yearTo - state.yearFrom === 9 && state.yearFrom % 10 === 0
      ? state.yearFrom
      : null;

  return (
    <div className={styles.overlay}>
      <button type="button" className={styles.scrim} aria-label="Close filters" onClick={onClose} />
      <div className={styles.sheet} role="dialog" aria-label="Filter the directory">
        <div className={styles.head}>
          <span className={styles.title}>Filter</span>
          <button type="button" className={styles.close} onClick={onClose} aria-label="Close">
            <X size={20} strokeWidth={3} aria-hidden="true" />
          </button>
        </div>

        <div className={styles.body}>
          <Section
            label="Place"
            value={sum.region}
            open={openKey === "region"}
            onToggle={() => toggle("region")}
            accent="blue"
          >
            <select
              className={styles.select}
              aria-label="Place"
              value={state.place ?? ""}
              onChange={(e) => patch({ place: e.target.value || null })}
            >
              <option value="">All places</option>
              {places.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </Section>

          <Section
            label="Year"
            value={sum.years}
            open={openKey === "year"}
            onToggle={() => toggle("year")}
          >
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
              <span aria-hidden="true">—</span>
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
          </Section>

          <Section
            label="Order"
            value={state.order === "oldest" ? "Oldest first" : "Newest first"}
            open={openKey === "order"}
            onToggle={() => toggle("order")}
          >
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
          </Section>

          <Section
            label="Visual access"
            value={sum.visual}
            open={openKey === "visual"}
            onToggle={() => toggle("visual")}
          >
            <div className={styles.order}>
              {VISUAL_OPTIONS.map(([v, l]) => (
                <button
                  key={v}
                  type="button"
                  className={styles.orderBtn}
                  data-on={state.visual === v || undefined}
                  aria-pressed={state.visual === v}
                  onClick={() => patch({ visual: v })}
                >
                  {l}
                </button>
              ))}
            </div>
          </Section>

          <Section
            label="Theme"
            value={sum.themes}
            open={openKey === "theme"}
            onToggle={() => toggle("theme")}
            accent="green"
          >
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
                    style={on ? { background: themeInk(t), borderColor: themeInk(t) } : undefined}
                    aria-pressed={on}
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
          </Section>
        </div>

        <button type="button" className={styles.apply} onClick={onClose}>
          Show {String(count).padStart(3, "0")} {count === 1 ? "object" : "objects"}
        </button>
      </div>
    </div>
  );
}

function Section({
  label,
  value,
  open,
  onToggle,
  accent,
  children,
}: {
  label: string;
  value: string;
  open: boolean;
  onToggle: () => void;
  accent?: "blue" | "green";
  children: ReactNode;
}) {
  return (
    <div className={styles.section} data-open={open || undefined}>
      <button type="button" className={styles.sectionHead} aria-expanded={open} onClick={onToggle}>
        <span className={styles.sectionLabel} data-accent={accent}>
          {label}
        </span>
        <span className={styles.sectionValue}>{value}</span>
        <ChevronDown size={18} strokeWidth={3} aria-hidden="true" data-open={open || undefined} />
      </button>
      {open ? <div className={styles.sectionBody}>{children}</div> : null}
    </div>
  );
}
