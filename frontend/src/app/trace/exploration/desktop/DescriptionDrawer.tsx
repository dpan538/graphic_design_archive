"use client";

import { useMemo } from "react";
import SystemSuggestionsPanel from "@/features/system-suggestions/ui/SystemSuggestionsPanel";
import type { ExplorationReference } from "@/features/system-suggestions/types";
import type { ExplorationViewDto } from "@/features/trace-v49/exploration-view/types";
import { ASSOCIATION_BASIS, ASSOCIATION_DETAILS, ASSOCIATION_ENDPOINTS, ASSOCIATION_SOURCES, ASSOCIATION_SOURCES_NOT_PUBLIC, DESCRIPTION, DESCRIPTION_CLOSE, PRESENTATION, PRESENTATION_NOTE, PROVENANCE, QUALIFIED_ASSOCIATIONS, SUGGESTS_BOUNDARY, VISIBLE_TERMS, WHAT_IS_SHOWN } from "../lib/content";
import styles from "./Drawer.module.css";

/* DESCRIPTION (§7i): what the current picture expresses. System suggests
   first — the reading entry, in its own bounded card, narration only —
   then the deterministic counterpart, WHAT IS SHOWN (the exact terms and
   association pairs the V2 state supplies), then PRESENTATION (the
   treatment, and that it carries no meaning), then the provenance folded.
   Nothing here repeats the rail. No hash, confidence or strength. */

export interface DescriptionDrawerProps {
  readonly view: ExplorationViewDto;
  readonly onClose: () => void;
}

export default function DescriptionDrawer({ view, onClose }: DescriptionDrawerProps) {
  const terms = view.map.nodes;
  const associations = view.map.associations;
  const ordered = useMemo(
    () => view.map.plain_text_tree.tree_node_ids.map((id) => terms.find((node) => node.vocabulary_id === id)?.canonical_label ?? "").filter(Boolean),
    [view.map.plain_text_tree.tree_node_ids, terms],
  );
  /* the state's identity, not its facts: the server reads the visible terms and associations itself
     and confirms the counts this drawer shows; the template is presentation and never enters */
  const reference = useMemo<ExplorationReference>(() => ({ mapId: view.restore.map_id, stateId: view.restore.state_id }), [view.restore.map_id, view.restore.state_id]);
  const shown = useMemo(() => ({ visibleTerms: terms.length, qualifiedAssociations: associations.length }), [terms.length, associations.length]);
  void ordered;

  return (
    <div className={styles.drawer}>
      <div className={styles.head}>
        <h2 className={styles.title}>{DESCRIPTION}</h2>
        <button type="button" className={styles.close} aria-label={DESCRIPTION_CLOSE} onClick={onClose}>×</button>
      </div>

      <section className={styles.suggestsCard} aria-label="System suggests">
        <SystemSuggestionsPanel surface="TRACE_VALIDATED_EXPLORATION" reference={reference} shown={shown} tone="canvas" variant="block" maxActions={0} />
      </section>
      <p className={styles.boundary}>{SUGGESTS_BOUNDARY}</p>

      <section className={styles.section} aria-labelledby="exploration-shown-heading">
        <h3 id="exploration-shown-heading" className={styles.sectionTitle}>{WHAT_IS_SHOWN}</h3>
        <p className={styles.counts}>{VISIBLE_TERMS(terms.length)} · {QUALIFIED_ASSOCIATIONS(associations.length)}</p>
        <ul role="list" className={styles.ledger}>
          {associations.map((item) => (
            <li key={item.association_id} className={styles.ledgerRow}>
              <span className={styles.pair}>{item.endpoint_labels[0]} — {item.endpoint_labels[1]}</span>
              {/* the association's details: the program's entry, never a generated action — the two endpoints,
                  the public basis, and the sources, which this release does not publish */}
              <details className={styles.fold} data-association-details={item.association_id}>
                <summary>{ASSOCIATION_DETAILS}</summary>
                <dl className={styles.facts}>
                  <div>
                    <dt>{ASSOCIATION_ENDPOINTS}</dt>
                    <dd>{item.endpoint_labels[0]} · {item.endpoint_labels[1]}</dd>
                  </div>
                  <div>
                    <dt>{ASSOCIATION_BASIS}</dt>
                    <dd>{item.association_accessible_description.trim() || SUGGESTS_BOUNDARY}</dd>
                  </div>
                  <div>
                    <dt>{ASSOCIATION_SOURCES}</dt>
                    <dd>{ASSOCIATION_SOURCES_NOT_PUBLIC}</dd>
                  </div>
                </dl>
              </details>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.section} aria-labelledby="exploration-presentation-heading">
        <h3 id="exploration-presentation-heading" className={styles.sectionTitle}>{PRESENTATION}</h3>
        <p className={styles.counts}>{view.presentation.template_name} · {view.presentation.variant_name}</p>
        <p className={styles.small}>{PRESENTATION_NOTE}</p>
      </section>

      <details className={styles.fold}>
        <summary>{PROVENANCE}</summary>
        <p className={styles.small}>Release v49 · Exploration V2 state {view.restore.state_id} · composition {view.map.composition.composition_id} · {view.map.composition.topology_family.toLowerCase().replaceAll("_", " ")} · presentation {view.presentation.presentation_version} · palette {view.presentation.palette_id}.</p>
      </details>
    </div>
  );
}
