"use client";

import type { ExplorationStartingPointDto, ExplorationViewAction, ExplorationViewDto } from "@/features/trace-v49/exploration-view/types";
import {
  ANOTHER_VIEW,
  ANOTHER_VIEW_NOTE,
  AT_RICHEST,
  AT_SIMPLEST,
  CATEGORY_WORDS,
  CHANGE,
  CHOOSER_CLOSE,
  CHOOSE_NOTE,
  CHOOSE_TITLE,
  COMPLEXITY,
  CURRENT,
  EXPORT,
  EXPORTING,
  EXPORT_NOTE,
  KICKER,
  LESS,
  MORE,
  NAME,
  OPEN_INQUIRY,
  ONLY_SIZE,
  OPEN_INQUIRY_COUNT,
  SINGLE_VIEW,
  STARTING_POINT,
  STATEMENT,
  TERMS,
} from "../lib/content";
import styles from "./ExplorationRail.module.css";

/* the rail (§7i). NORMAL: the page's identity; STARTING POINT as one
   unmistakable current state — the word, its category, CHANGE; then the
   controls in the owner's order — COMPLEXITY, ANOTHER VIEW, EXPORT — and,
   set apart at the foot, the secondary entry to Open Inquiry. SELECTION
   (after CHANGE): the rail becomes one task — the twenty-six words in
   their four governed groups, the current one marked and not a candidate,
   KEEP CURRENT STARTING POINT to leave — and the other controls are
   hidden until a word is chosen or the state is left. */

export interface ExplorationRailProps {
  readonly view: ExplorationViewDto;
  readonly startingPoints: readonly ExplorationStartingPointDto[];
  readonly inquiryCount: number;
  readonly inquiryOpen: boolean;
  readonly choosing: boolean;
  readonly pending: string | null;
  readonly locked: boolean;
  readonly onChoosing: (open: boolean) => void;
  readonly onStart: (vocabularyId: string) => void;
  readonly onAction: (action: ExplorationViewAction) => void;
  readonly onExport: () => void;
  readonly onOpenInquiry: () => void;
}

const CATEGORY_ORDER = ["theme", "region", "movement", "medium"] as const;

export default function ExplorationRail({ view, startingPoints, inquiryCount, inquiryOpen, choosing, pending, locked, onChoosing, onStart, onAction, onExport, onOpenInquiry }: ExplorationRailProps) {
  const terms = view.map.nodes.length;
  const { more, less, another_view: another } = view.controls;

  if (choosing) {
    return (
      <div className={styles.rail} data-state="choosing">
        <header className={styles.header}>
          <p className={styles.kicker}>{KICKER}</p>
          <h1 className={styles.name}>{NAME}</h1>
        </header>
        <section className={styles.block} aria-labelledby="exploration-choose-heading">
          <h2 id="exploration-choose-heading" className={styles.label}>{STARTING_POINT}</h2>
          <button type="button" className={styles.keep} disabled={locked} onClick={() => onChoosing(false)}>
            {CHOOSER_CLOSE}
          </button>
          <p className={styles.note}>{CHOOSE_NOTE}</p>
        </section>
        <div id="exploration-chooser" className={styles.chooser} role="group" aria-label={CHOOSE_TITLE}>
          {CATEGORY_ORDER.map((category) => {
            const items = startingPoints.filter((point) => point.category_id === category);
            if (items.length === 0) return null;
            return (
              <section key={category} className={styles.group} aria-label={CATEGORY_WORDS[category] ?? category}>
                <p className={styles.groupWord}>{CATEGORY_WORDS[category] ?? category}</p>
                <ul role="list" className={styles.words}>
                  {items.map((point) => {
                    const current = point.vocabulary_id === view.starting_point.vocabulary_id;
                    return (
                      <li key={point.vocabulary_id}>
                        {current ? (
                          <div className={styles.wordCurrent} aria-current="true">
                            <span className={styles.check} aria-hidden="true">✓</span>
                            <span className={styles.wordText}>{point.label}</span>
                            <span className={styles.wordState}>{CURRENT}</span>
                          </div>
                        ) : (
                          <button
                            type="button"
                            className={styles.word}
                            disabled={locked}
                            onClick={() => { onChoosing(false); onStart(point.vocabulary_id); }}
                          >
                            <span className={styles.wordText}>{point.label}</span>
                          </button>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.rail} data-state="normal">
      <header className={styles.header}>
        <p className={styles.kicker}>{KICKER}</p>
        <h1 className={styles.name}>{NAME}</h1>
        <p className={styles.statement}>{STATEMENT}</p>
      </header>

      {/* 1 — the starting point: the current state, and the way to change it */}
      <section className={styles.block} aria-labelledby="exploration-start-heading">
        <h2 id="exploration-start-heading" className={styles.label}>{STARTING_POINT}</h2>
        <p className={styles.current}>{view.starting_point.label}</p>
        <p className={styles.note}>{view.starting_point.category_label}</p>
        <button type="button" className={styles.change} aria-controls="exploration-chooser" disabled={locked} onClick={() => onChoosing(true)}>
          {CHANGE}
        </button>
      </section>

      {/* 2 — complexity: the visible term count, nothing else */}
      <section className={styles.block} aria-labelledby="exploration-complexity-heading">
        <h2 id="exploration-complexity-heading" className={styles.label}>{COMPLEXITY}</h2>
        <div className={styles.complexity}>
          <button
            type="button"
            className={styles.step}
            aria-label={less.available ? `${LESS}: ${TERMS(less.next_visible_count ?? terms - 1)}` : AT_SIMPLEST}
            aria-disabled={!less.available || locked || undefined}
            title={less.available ? LESS : AT_SIMPLEST}
            onClick={() => { if (less.available && !locked) onAction("LESS"); }}
          >
            −
          </button>
          <p className={styles.count} aria-live="polite">
            <b>{terms}</b> {terms === 1 ? "term" : "terms"}
          </p>
          <button
            type="button"
            className={styles.step}
            aria-label={more.available ? `${MORE}: ${TERMS(more.next_visible_count ?? terms + 1)}` : AT_RICHEST}
            aria-disabled={!more.available || locked || undefined}
            title={more.available ? MORE : AT_RICHEST}
            onClick={() => { if (more.available && !locked) onAction("MORE"); }}
          >
            +
          </button>
        </div>
        {!more.available || !less.available ? (
          <p className={styles.note}>{!more.available && !less.available ? ONLY_SIZE : !more.available ? AT_RICHEST : AT_SIMPLEST}</p>
        ) : null}
      </section>

      {/* 3 — another view: the same starting point, another governed composition, another treatment */}
      <section className={styles.block} aria-labelledby="exploration-another-heading">
        <h2 id="exploration-another-heading" className={styles.label}>{ANOTHER_VIEW}</h2>
        <p className={styles.note}>{another.available ? ANOTHER_VIEW_NOTE(another.position + 1, another.pool_size) : SINGLE_VIEW}</p>
        <button
          type="button"
          className={styles.action}
          aria-disabled={!another.available || locked || undefined}
          onClick={() => { if (another.available && !locked) onAction("ANOTHER_VIEW"); }}
        >
          <span className={styles.actionWord}>{pending === "ANOTHER_VIEW" ? "…" : ANOTHER_VIEW}</span>
        </button>
      </section>

      {/* 4 — export: the stamp as shown */}
      <section className={styles.block} aria-labelledby="exploration-export-heading">
        <h2 id="exploration-export-heading" className={styles.label}>{EXPORT}</h2>
        <button type="button" className={styles.action} aria-disabled={locked || undefined} onClick={() => { if (!locked) onExport(); }}>
          <span className={styles.actionWord}>{pending === "EXPORT" ? EXPORTING : EXPORT}</span>
          <span className={styles.actionNote}>{EXPORT_NOTE(view.presentation.form_name, view.presentation.form_dimensions.width, view.presentation.form_dimensions.height)}</span>
        </button>
      </section>

      {/* the secondary entry: Open Inquiry, a reading layer beside the view */}
      <section className={styles.inquiry} aria-labelledby="exploration-inquiry-heading">
        <button type="button" className={styles.inquiryEntry} aria-expanded={inquiryOpen} aria-controls="exploration-drawer" onClick={onOpenInquiry}>
          <span id="exploration-inquiry-heading" className={styles.inquiryWord}>{OPEN_INQUIRY} · {inquiryCount}</span>
          <span className={styles.inquiryNote}>{OPEN_INQUIRY_COUNT(inquiryCount)}</span>
          <span className={styles.inquiryArrow} aria-hidden="true">→</span>
        </button>
      </section>
    </div>
  );
}
