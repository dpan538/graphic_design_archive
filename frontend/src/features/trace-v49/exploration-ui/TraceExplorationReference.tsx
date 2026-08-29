"use client";

import Link from "next/link";
import { useMemo } from "react";
import SystemSuggestionsPanel from "@/features/system-suggestions/ui/SystemSuggestionsPanel";
import type { ApprovedSuggestion, TraceSuggestionContext } from "@/features/system-suggestions/types";
import styles from "./TraceExplorationReference.module.css";

export type TraceExplorationReferenceProps = {
  validated: {
    conceptCount: number;
    associationCount: number;
    compositionCount: number;
    labels: readonly string[];
  };
  openInquiry: {
    recordCount: number;
    governedIdentityCount: number;
    labels: readonly string[];
  };
};

function focusElement(id: string): void {
  const element = document.getElementById(id);
  element?.focus();
  element?.scrollIntoView({ behavior: "smooth", block: "center" });
}

export default function TraceExplorationReference({ validated, openInquiry }: TraceExplorationReferenceProps) {
  const validatedContext = useMemo<TraceSuggestionContext>(() => ({
    stateType: "VALIDATED_EXPLORATION_OVERVIEW",
    labels: validated.labels,
    counts: {
      validatedConcepts: validated.conceptCount,
      validatedAssociations: validated.associationCount,
      validatedCompositions: validated.compositionCount,
    },
    validActionIds: validated.compositionCount > 0
      ? ["FOCUS_VALIDATED_NODE", "REVIEW_VALIDATED_ASSOCIATION", "RETURN_TO_COMPOSITION"]
      : [],
    evidenceClass: "VALIDATED",
  }), [validated]);
  const inquiryContext = useMemo<TraceSuggestionContext>(() => ({
    stateType: "OPEN_INQUIRY_OVERVIEW",
    labels: openInquiry.labels,
    counts: { openInquiryRecords: openInquiry.recordCount, governedInquiryIdentities: openInquiry.governedIdentityCount },
    validActionIds: ["REVIEW_EVIDENCE_GAP", "REVIEW_SOURCE_BOUNDARY", "RETURN_TO_VALIDATED_EXPLORATION"],
    evidenceClass: "OPEN_INQUIRY",
  }), [openInquiry]);

  function validatedAction(suggestion: ApprovedSuggestion) {
    const actionId = suggestion.action.parameters.actionId;
    if (actionId === "FOCUS_VALIDATED_NODE") focusElement("validated-concepts");
    else if (actionId === "REVIEW_VALIDATED_ASSOCIATION") focusElement("validated-associations");
    else if (actionId === "RETURN_TO_COMPOSITION") focusElement("validated-compositions");
  }

  function inquiryAction(suggestion: ApprovedSuggestion) {
    const actionId = suggestion.action.parameters.actionId;
    if (actionId === "REVIEW_EVIDENCE_GAP") focusElement("open-inquiry-evidence-gap");
    else if (actionId === "REVIEW_SOURCE_BOUNDARY") focusElement("open-inquiry-source-boundary");
    else if (actionId === "RETURN_TO_VALIDATED_EXPLORATION") focusElement("validated-exploration");
  }

  return (
    <main className={styles.workspace}>
      <p className={styles.eyebrow}>TRACE · desktop research environment</p>
      <h1>Research context and exploration</h1>
      <p>TRACE keeps contextual views, validated product facts, and unresolved inquiry in separate evidence-governed layers.</p>

      <nav className={styles.functionLinks} aria-label="TRACE functions">
        <Link href="/trace/context-canvas"><strong>Context Canvas</strong><span>Public project-curated medium, theme, and movement context.</span></Link>
        <Link href="/trace/spacetime"><strong>Spacetime</strong><span>Recorded temporal and geographic aggregate context.</span></Link>
      </nav>

      <div className={styles.layers}>
        <section id="validated-exploration" className={styles.layer} tabIndex={-1}>
          <p className={styles.eyebrow}>Exploration layer</p>
          <h2>Validated Exploration</h2>
          <p>{validated.compositionCount > 0 ? "Only active product facts are available in this layer." : "No validated composition is active in this release."}</p>
          <ul className={styles.counts}>
            <li id="validated-concepts" className={styles.focusTarget} tabIndex={-1}>{validated.conceptCount} concepts</li>
            <li id="validated-associations" className={styles.focusTarget} tabIndex={-1}>{validated.associationCount} associations</li>
            <li id="validated-compositions" className={styles.focusTarget} tabIndex={-1}>{validated.compositionCount} compositions</li>
          </ul>
          <SystemSuggestionsPanel surface="TRACE_VALIDATED_EXPLORATION" context={validatedContext} onAction={validatedAction} />
        </section>

        <section className={styles.layer}>
          <p className={styles.eyebrow}>Separate unresolved layer</p>
          <SystemSuggestionsPanel surface="TRACE_OPEN_INQUIRY" context={inquiryContext} onAction={inquiryAction} openInquiryDisclosure />
          <p id="open-inquiry-evidence-gap" className={styles.focusTarget} tabIndex={-1}>{openInquiry.recordCount} bounded records remain unresolved and inactive.</p>
          <p id="open-inquiry-source-boundary" className={styles.focusTarget} tabIndex={-1}>{openInquiry.governedIdentityCount} records have governed inquiry-only identities; none may enter validated topology.</p>
        </section>
      </div>
    </main>
  );
}
