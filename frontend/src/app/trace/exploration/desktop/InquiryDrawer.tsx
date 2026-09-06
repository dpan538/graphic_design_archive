"use client";

import { useMemo, type RefObject } from "react";
import SystemSuggestionsPanel from "@/features/system-suggestions/ui/SystemSuggestionsPanel";
import type { InquiryReference } from "@/features/system-suggestions/types";
import {
  INQUIRY_BACK,
  INQUIRY_CHOOSE,
  INQUIRY_EVIDENCE_GAP,
  INQUIRY_EVIDENCE_GAP_TEXT,
  INQUIRY_FORM,
  INQUIRY_KIND,
  INQUIRY_PROVENANCE,
  INQUIRY_SCOPE,
  INQUIRY_SOURCE_BOUNDARY,
  INQUIRY_SOURCE_BOUNDARY_TEXT,
  OPEN_INQUIRY_DISCLOSURE,
} from "../lib/content";
import styles from "./Drawer.module.css";

/* Open Inquiry (§7i): a reading layer beside the view, never a peer mode.
   The drawer always begins, in this order, with "Open inquiry", "Evidence
   remains incomplete." and "This is not a validated historical
   association."; only after them the questions, one at a time, and at the
   foot System suggests bounded to the question. Nothing here enters the
   view, its controls, its candidates or its export. */

export interface InquiryItem {
  readonly inquiryId: string;
  readonly participants: readonly string[];
  readonly boundedScope: string;
  readonly relationForm: string;
  readonly governed: boolean;
}

export interface InquiryDrawerProps {
  readonly items: readonly InquiryItem[];
  readonly selected: number | null;
  readonly onSelect: (index: number | null) => void;
  readonly onClose: () => void;
  readonly sourceBoundaryRef: RefObject<HTMLParagraphElement | null>;
  readonly onSuggestion: (actionId: string) => void;
}

export default function InquiryDrawer({ items, selected, onSelect, onClose, sourceBoundaryRef, onSuggestion }: InquiryDrawerProps) {
  const item = selected === null ? null : items[selected] ?? null;
  /* the inquiry's identity: the server reads its participants and scope from the public registry */
  const reference = useMemo<InquiryReference | null>(() => item ? { inquiryId: item.inquiryId } : null, [item]);
  const shown = useMemo(() => item ? { participants: item.participants.length } : undefined, [item]);

  return (
    <div className={styles.drawer}>
      <div className={styles.head}>
        <h2 className={styles.title}>{OPEN_INQUIRY_DISCLOSURE[0]}</h2>
        <button type="button" className={styles.close} aria-label="Close Open inquiry" onClick={onClose}>×</button>
      </div>
      <p className={styles.disclosure} data-open-inquiry-disclosure="true">{OPEN_INQUIRY_DISCLOSURE[1]}</p>
      <p className={styles.disclosure}>{OPEN_INQUIRY_DISCLOSURE[2]}</p>
      <hr className={styles.rule} />

      {item === null ? (
        <>
          <p className={styles.small}>{INQUIRY_CHOOSE}</p>
          <ol className={styles.questions}>
            {items.map((entry, index) => (
              <li key={entry.inquiryId}>
                <button type="button" className={styles.question} onClick={() => onSelect(index)}>
                  <span className={styles.questionIndex}>{String(index + 1).padStart(2, "0")}</span>
                  <span className={styles.questionWords}>{entry.participants.join(" · ")}</span>
                  <span className={styles.questionNote}>{entry.participants.length} terms · {INQUIRY_KIND}</span>
                </button>
              </li>
            ))}
          </ol>
        </>
      ) : (
        <>
          <button type="button" className={styles.back} onClick={() => onSelect(null)}>‹ {INQUIRY_BACK}</button>
          <h3 className={styles.questionTitle}>{item.participants.join(" · ")}</h3>
          <dl className={styles.facts}>
            <div>
              <dt>{INQUIRY_SCOPE}</dt>
              <dd>{item.boundedScope}</dd>
            </div>
            <div>
              <dt>{INQUIRY_EVIDENCE_GAP}</dt>
              <dd>{INQUIRY_EVIDENCE_GAP_TEXT}</dd>
            </div>
            <div>
              <dt>{INQUIRY_SOURCE_BOUNDARY}</dt>
              <dd><p ref={sourceBoundaryRef} tabIndex={-1} className={styles.focusable}>{INQUIRY_SOURCE_BOUNDARY_TEXT}</p></dd>
            </div>
          </dl>
          <details className={styles.fold}>
            <summary>{INQUIRY_PROVENANCE}</summary>
            <p className={styles.small}>{INQUIRY_FORM}: {item.relationForm.toLowerCase().replaceAll("_", " ")} · {item.inquiryId}</p>
          </details>
          {reference ? (
            <div className={styles.suggests}>
              <SystemSuggestionsPanel surface="TRACE_OPEN_INQUIRY" reference={reference} shown={shown} onAction={(suggestion) => onSuggestion(String(suggestion.action.parameters.actionId))} tone="canvas" variant="block" maxActions={1} />
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
