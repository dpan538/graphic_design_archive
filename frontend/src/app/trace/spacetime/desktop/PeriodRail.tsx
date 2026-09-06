"use client";

import { useRef, useState, type KeyboardEvent } from "react";
import type { PublicSpacetimePeriod } from "@/features/trace-v49/spacetime/governed/types";
import type { SpacetimeLayer, SpacetimeTemporalSeries } from "@/features/trace-v49/spacetime/map";
import type { YearCount } from "../lib/years.server";
import { PERIODS_LABEL, RAIL_ABOUT, RAIL_COLUMNS, RAIL_OVERLAP, RECORDS, WINDOW_WORDS } from "../lib/content";
import styles from "./PeriodRail.module.css";

/* 02 — the period rail (§7h): a temporal instrument above the map. One
   column a year, 1800 to 2026 — public records by recorded year, on a
   square root; the governed decades as the units of choice, exactly one
   chosen, its columns in signal red; every fifty years the full year,
   between them the decade's short form. In the TEMPORAL layer the
   three-period window is shown as such — the previous and next decades
   in cobalt, the rest faded, the words PREVIOUS · CURRENT · NEXT under
   them — so every glyph on the map is read against the same three. A
   selected place adds its own three counts under the window. No
   animation, no interpolation, no year range. Arrow keys move the
   choice. */

export interface PeriodRailProps {
  readonly periods: readonly PublicSpacetimePeriod[];
  readonly years: readonly YearCount[];
  readonly selectedPeriodId: string;
  readonly layer: SpacetimeLayer;
  readonly place: SpacetimeTemporalSeries | null;
  readonly busy: boolean;
  readonly onSelect: (periodId: string) => void;
}

const H = 40;
const FIRST = 1800;

const decadeWord = (start: number) => (start % 50 === 0 ? String(start) : `${String(start).slice(2)}s`);

export default function PeriodRail({ periods, years, selectedPeriodId, layer, place, busy, onSelect }: PeriodRailProps) {
  const listRef = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<string | null>(null);
  const span = years.length;
  const most = Math.max(1, ...years.map((entry) => entry.count));
  const heightFor = (count: number) => (count === 0 ? 0 : Math.max(1.5, H * Math.sqrt(count / most)));
  const selectedIndex = periods.findIndex((period) => period.periodId === selectedPeriodId);
  const windowRole = (index: number): "previous" | "current" | "next" | null =>
    index === selectedIndex ? "current" : index === selectedIndex - 1 ? "previous" : index === selectedIndex + 1 ? "next" : null;
  const placeMost = place ? Math.max(1, place.previous?.records ?? 0, place.current?.records ?? 0, place.next?.records ?? 0) : 1;

  function onKey(event: KeyboardEvent<HTMLDivElement>) {
    if (selectedIndex < 0) return;
    const next = event.key === "ArrowRight" ? selectedIndex + 1
      : event.key === "ArrowLeft" ? selectedIndex - 1
        : event.key === "Home" ? 0
          : event.key === "End" ? periods.length - 1
            : null;
    if (next === null || next < 0 || next >= periods.length) return;
    event.preventDefault();
    onSelect(periods[next].periodId);
    listRef.current?.querySelectorAll<HTMLButtonElement>("button")[next]?.focus();
  }

  return (
    <div className={styles.rail} data-layer={layer} aria-busy={busy || undefined}>
      <svg className={styles.columns} viewBox={`0 0 ${span} ${H}`} preserveAspectRatio="none" aria-hidden="true">
        {periods.map((period, index) => {
          const role = windowRole(index);
          return (
            <g key={period.periodId} data-role={role ?? undefined} data-hover={hover === period.periodId || undefined}>
              {years
                .filter((entry) => entry.year >= period.startYearInclusive && entry.year < period.endYearExclusive)
                .map((entry) => (
                  <rect
                    key={entry.year}
                    x={entry.year - FIRST + 0.12}
                    y={H - heightFor(entry.count)}
                    width={0.76}
                    height={heightFor(entry.count)}
                  />
                ))}
            </g>
          );
        })}
      </svg>
      <div
        ref={listRef}
        className={styles.decades}
        role="radiogroup"
        aria-label={PERIODS_LABEL}
        onKeyDown={onKey}
      >
        {periods.map((period, index) => {
          const role = windowRole(index);
          const width = (Math.min(period.endYearExclusive, FIRST + span) - period.startYearInclusive) / span;
          return (
            <button
              key={period.periodId}
              type="button"
              role="radio"
              aria-checked={role === "current"}
              tabIndex={role === "current" ? 0 : -1}
              className={`${styles.decade} tnum`}
              data-role={role ?? undefined}
              data-full={period.startYearInclusive % 50 === 0 || undefined}
              style={{ left: `${((period.startYearInclusive - FIRST) / span) * 100}%`, width: `${width * 100}%` }}
              aria-label={`${period.label}: ${RECORDS(period.recordCount)}`}
              title={`${period.label} · ${RECORDS(period.recordCount)}`}
              onClick={() => onSelect(period.periodId)}
              onMouseEnter={() => setHover(period.periodId)}
              onMouseLeave={() => setHover((current) => (current === period.periodId ? null : current))}
              onFocus={() => setHover(period.periodId)}
              onBlur={() => setHover((current) => (current === period.periodId ? null : current))}
            >
              <span>{decadeWord(period.startYearInclusive)}</span>
              {layer === "temporal" && role ? <span className={styles.windowWord}>{WINDOW_WORDS[role]}</span> : null}
            </button>
          );
        })}
      </div>
      {place ? (
        <div className={styles.place} aria-label={`${place.label}: records in the previous, this and the next period`}>
          {periods.map((period, index) => {
            const role = windowRole(index);
            if (!role) return null;
            const stat = role === "previous" ? place.previous : role === "current" ? place.current : place.next;
            const width = (Math.min(period.endYearExclusive, FIRST + span) - period.startYearInclusive) / span;
            return (
              <span
                key={period.periodId}
                className={`${styles.placeCell} tnum`}
                data-role={role}
                style={{ left: `${((period.startYearInclusive - FIRST) / span) * 100}%`, width: `${width * 100}%` }}
                title={stat ? `${place.label} · ${period.label} · ${RECORDS(stat.records)}` : undefined}
              >
                <span className={styles.placeBar} style={{ height: `${stat ? Math.max(stat.records > 0 ? 2 : 0, 14 * Math.sqrt(stat.records / placeMost)) : 0}px` }} aria-hidden="true" />
                <span className={styles.placeCount}>{stat ? stat.records.toLocaleString("en-US") : "—"}</span>
              </span>
            );
          })}
          <span className={styles.placeName}>{place.label}</span>
        </div>
      ) : null}
      <div className={styles.note}>
        <span>{RAIL_COLUMNS}</span>
        <details className={styles.about}>
          <summary className={styles.aboutWord}>{RAIL_ABOUT}</summary>
          <span className={styles.aboutText}>{RAIL_OVERLAP}</span>
        </details>
      </div>
    </div>
  );
}
