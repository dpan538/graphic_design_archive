"use client";

import SystemSuggestionsPanel from "@/features/system-suggestions/ui/SystemSuggestionsPanel";
import type { ApprovedSuggestion, TraceSuggestionContext } from "@/features/system-suggestions/types";
import type {
  PublicSpacetimeAccessibleGeographyRow,
  PublicSpacetimeAtlasDataset,
  PublicSpacetimeMappedGeography,
  PublicSpacetimeNonMappedGeography,
} from "@/features/trace-v49/spacetime/governed/types";
import type { SpacetimeTemporalSeries } from "@/features/trace-v49/spacetime/map";
import {
  AROUND_PERIOD,
  CLASS_WORDS,
  DATA_QUALITY,
  PLACE_PROFILE,
  PROJECTION,
  QUALIFICATION,
  RANK_OF,
  RECORDS,
  RELEASE,
  ROW_RANK,
  ROW_RECORDS,
  ROW_SHARE,
  SHARE_OF_PERIOD,
  SHARE_SHORT,
  STATE_NOTES,
  STATE_WORDS,
  TECHNICAL,
  UNAVAILABLE,
  VIEW_RECORDS,
  WORLD_VIEW,
  precisionLine,
} from "../lib/content";
import styles from "./PlaceProfile.module.css";

/* 03 — PLACE PROFILE (§7h): the right column, open once a place is
   chosen. How this place behaves around this period, as archive
   composition: its records, its share of the period's public records,
   its rank among the period's recorded geographies; then the temporal
   window — records, share and rank in the previous, this and the next
   period, from the three governed atlases; "not plotted" said plainly
   only when it applies; how the records are dated behind Data quality;
   the qualification when the atlas carries one; two ways on; the
   release folded. At its foot, and only here, System suggests. */

export interface PlaceProfileProps {
  readonly atlas: PublicSpacetimeAtlasDataset;
  readonly row: PublicSpacetimeAccessibleGeographyRow;
  readonly detail: PublicSpacetimeMappedGeography | PublicSpacetimeNonMappedGeography | null;
  readonly series: SpacetimeTemporalSeries | null;
  readonly windowState: "idle" | "loading" | "ready" | "error";
  readonly guidanceReady: boolean;
  readonly suggestionContext: TraceSuggestionContext;
  readonly onSuggestion: (suggestion: ApprovedSuggestion) => void;
  readonly onViewRecords: () => void;
  readonly onWorldView: () => void;
}

export default function PlaceProfile({
  atlas,
  row,
  detail,
  series,
  windowState,
  guidanceReady,
  suggestionContext,
  onSuggestion,
  onViewRecords,
  onWorldView,
}: PlaceProfileProps) {
  const period = atlas.selectedPeriod.label;
  const current = series?.current ?? null;
  const share = row.denominator > 0 ? row.recordCount / row.denominator : 0;
  const plotted = row.mappingState === "mapped";
  const columns = [series?.previous ?? null, current, series?.next ?? null] as const;
  const cell = (value: string | null) => (windowState === "loading" && value === null ? "…" : value ?? UNAVAILABLE);
  return (
    <aside id="spacetime-place-profile" className={styles.panel} aria-labelledby="place-profile-heading">
      <h2 id="place-profile-heading" className={styles.heading}>{PLACE_PROFILE}</h2>

      <div className={styles.identity}>
        <p className={styles.label} title={row.label}>{row.label}</p>
        <p className={styles.kind}>
          {detail ? <span>{CLASS_WORDS[detail.geographyClass]}</span> : null}
          {!plotted ? <span className={styles.unplotted} data-state={row.mappingState}>{STATE_WORDS[row.mappingState]}</span> : null}
        </p>
        {!plotted && STATE_NOTES[row.mappingState] ? <p className={styles.note}>{STATE_NOTES[row.mappingState]}</p> : null}
      </div>

      <div className={styles.now}>
        <p className={`${styles.period} tnum`}>{period}</p>
        <p className={`${styles.records} tnum`}>{RECORDS(row.recordCount)} · {SHARE_OF_PERIOD(share)}</p>
        {current && current.rank > 0 ? <p className={`${styles.rank} tnum`}>{RANK_OF(current.rank, current.geographies)}</p> : null}
      </div>

      <section className={styles.window} aria-labelledby="place-window-heading">
        <h3 id="place-window-heading" className={styles.subheading}>{AROUND_PERIOD}</h3>
        <table className={`${styles.grid} tnum`}>
          <thead>
            <tr>
              <th scope="col"><span className="sr-only">Measure</span></th>
              {columns.map((stat, index) => (
                <th key={index} scope="col" data-role={index === 1 ? "current" : undefined}>{stat?.label ?? (windowState === "loading" ? "…" : UNAVAILABLE)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">{ROW_RECORDS}</th>
              {columns.map((stat, index) => <td key={index} data-role={index === 1 ? "current" : undefined}>{cell(stat ? stat.records.toLocaleString("en-US") : null)}</td>)}
            </tr>
            <tr>
              <th scope="row">{ROW_SHARE}</th>
              {columns.map((stat, index) => <td key={index} data-role={index === 1 ? "current" : undefined}>{cell(stat ? SHARE_SHORT(stat.share) : null)}</td>)}
            </tr>
            <tr>
              <th scope="row">{ROW_RANK}</th>
              {columns.map((stat, index) => <td key={index} data-role={index === 1 ? "current" : undefined}>{cell(stat ? (stat.rank > 0 ? `#${stat.rank}` : UNAVAILABLE) : null)}</td>)}
            </tr>
          </tbody>
        </table>
      </section>

      <details className={styles.fold}>
        <summary className={styles.summary}>{DATA_QUALITY}</summary>
        <p className={`${styles.note} tnum`}>{precisionLine(row.precisionBreakdown) || UNAVAILABLE}</p>
        {!plotted && detail?.qualification ? (
          <>
            <p className={styles.subheading}>{QUALIFICATION}</p>
            <p className={styles.note}>{detail.qualification}</p>
          </>
        ) : null}
      </details>

      <div className={styles.actions}>
        <button type="button" className={styles.primary} onClick={onViewRecords}>{VIEW_RECORDS}</button>
        <button type="button" className={styles.secondary} onClick={onWorldView}>{WORLD_VIEW}</button>
      </div>

      <details className={styles.fold}>
        <summary className={styles.summary}>{TECHNICAL}</summary>
        <dl className={styles.facts}>
          <div className={styles.fact}><dt>{RELEASE}</dt><dd className="tnum">{atlas.release.researchReleaseId}</dd></div>
          <div className={styles.fact}><dt>{PROJECTION}</dt><dd className="tnum">{atlas.release.spacetimeProjectionId}</dd></div>
        </dl>
      </details>

      {guidanceReady ? (
        <SystemSuggestionsPanel
          surface="TRACE_SPACETIME"
          context={suggestionContext}
          onAction={onSuggestion}
          tone="canvas"
          variant="block"
          maxActions={2}
        />
      ) : null}
    </aside>
  );
}
