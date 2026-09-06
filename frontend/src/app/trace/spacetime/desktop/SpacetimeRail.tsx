"use client";

import Link from "next/link";
import type { SpacetimeRendererMode } from "@/features/trace-v49/spacetime/gis";
import type { PublicSpacetimePeriod } from "@/features/trace-v49/spacetime/governed/types";
import type { SpacetimeLayer, SpacetimePeriodProfile } from "@/features/trace-v49/spacetime/map";
import {
  DATA_QUALITY,
  DATA_QUALITY_NOTE,
  GEOGRAPHIES,
  KICKER,
  LAYERS,
  LAYER_LABEL,
  MAPPED,
  NAME,
  NOT_MAPPED,
  PERIOD_LABEL,
  PUBLIC_RECORDS,
  RANKING_OPEN,
  RECORDS,
  SHARE_OF_PERIOD,
  STATEMENT,
  STYLE_LABEL,
  TOP_CONCENTRATION,
  VIEWS,
  VIEW_HELP,
  VIEW_NOTE,
  precisionLine,
} from "../lib/content";
import styles from "./SpacetimeRail.module.css";

/* 01 — the rail (§7h): the view's name and its one sentence; the PERIOD
   PROFILE — what this decade looks like: its public records, its
   recorded geographies, its top concentration and that place's share,
   the previous and next periods' totals beside it; how the records are
   dated and how many stand on the map behind "Data quality"; the MAP
   LAYER as the research control (Distribution · Temporal); the MAP
   STYLE as a small secondary choice; the way to the place ranking. */

export interface SpacetimeRailProps {
  readonly period: PublicSpacetimePeriod;
  readonly profile: SpacetimePeriodProfile;
  readonly layer: SpacetimeLayer;
  readonly mode: SpacetimeRendererMode;
  readonly rankingOpen: boolean;
  readonly onLayer: (layer: SpacetimeLayer) => void;
  readonly onMode: (mode: SpacetimeRendererMode) => void;
  readonly onRanking: () => void;
}

export default function SpacetimeRail({ period, profile, layer, mode, rankingOpen, onLayer, onMode, onRanking }: SpacetimeRailProps) {
  return (
    <div className={styles.rail}>
      <header className={styles.header}>
        <p className={styles.kicker}><Link href="/trace">{KICKER}</Link></p>
        <h1 className={styles.name}>{NAME}</h1>
        <p className={styles.statement}>{STATEMENT}</p>
      </header>

      <section className={styles.group} aria-labelledby="spacetime-period-heading">
        <h2 id="spacetime-period-heading" className={styles.label}>{PERIOD_LABEL}</h2>
        <p className={`${styles.period} tnum`}>{period.label}</p>
        <p className={`${styles.count} tnum`}>{PUBLIC_RECORDS(profile.records)}</p>
        <p className={`${styles.sub} tnum`}>{GEOGRAPHIES(profile.geographies)}</p>
        {profile.top ? (
          <div className={styles.top}>
            <p className={styles.label}>{TOP_CONCENTRATION}</p>
            <p className={styles.topPlace}>{profile.top.label}</p>
            <p className={`${styles.sub} tnum`}>{RECORDS(profile.top.records)} · {SHARE_OF_PERIOD(profile.top.share)}</p>
          </div>
        ) : null}
        <dl className={`${styles.window} tnum`}>
          <div data-role="previous"><dt>{profile.previous?.label ?? "—"}</dt><dd>{profile.previous ? RECORDS(profile.previous.records) : "—"}</dd></div>
          <div data-role="current"><dt>{period.label}</dt><dd>{RECORDS(profile.records)}</dd></div>
          <div data-role="next"><dt>{profile.next?.label ?? "—"}</dt><dd>{profile.next ? RECORDS(profile.next.records) : "—"}</dd></div>
        </dl>
        <details className={styles.fold}>
          <summary className={styles.summary}>{DATA_QUALITY}</summary>
          <p className={styles.sub}>{DATA_QUALITY_NOTE}</p>
          <p className={`${styles.sub} tnum`}>{MAPPED(period.mappedRecordCount)} · {NOT_MAPPED(period.unmappedRecordCount)}</p>
          <p className={`${styles.sub} tnum`}>{precisionLine(period.precisionBreakdown) || "—"}</p>
        </details>
      </section>

      <section className={styles.group} aria-labelledby="spacetime-layer-heading">
        <h2 id="spacetime-layer-heading" className={styles.label}>{LAYER_LABEL}</h2>
        <div className={styles.stack} role="radiogroup" aria-label={LAYER_LABEL}>
          {LAYERS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="radio"
              aria-checked={item.id === layer}
              className={styles.option}
              onClick={() => onLayer(item.id)}
            >
              <span className={styles.optionMark} aria-hidden="true" />
              <span className={styles.optionText}>
                <span className={styles.optionWord}>{item.label}</span>
                <span className={styles.optionBrief}>{item.brief}</span>
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className={styles.groupQuiet} aria-labelledby="spacetime-style-heading">
        <h2 id="spacetime-style-heading" className={styles.labelQuiet}>{STYLE_LABEL}</h2>
        <div className={styles.segments} role="radiogroup" aria-label={STYLE_LABEL}>
          {VIEWS.map((view) => (
            <button
              key={view.id}
              type="button"
              role="radio"
              aria-checked={view.id === mode}
              className={styles.segment}
              title={view.brief}
              onClick={() => onMode(view.id)}
            >
              {view.label}
            </button>
          ))}
        </div>
        <details className={styles.fold}>
          <summary className={styles.summaryQuiet}>{VIEW_HELP}</summary>
          <dl className={styles.help}>
            {VIEWS.map((view) => (
              <div key={view.id}>
                <dt>{view.label}</dt>
                <dd>{view.brief}</dd>
              </div>
            ))}
          </dl>
          <p className={styles.sub}>{VIEW_NOTE}</p>
        </details>
      </section>

      <button type="button" className={styles.table} aria-expanded={rankingOpen} aria-controls="spacetime-drawer" onClick={onRanking}>
        <span className={styles.tableWord}>{RANKING_OPEN}</span>
        <span className={`${styles.tableCount} tnum`}>{profile.geographies}</span>
      </button>
    </div>
  );
}
