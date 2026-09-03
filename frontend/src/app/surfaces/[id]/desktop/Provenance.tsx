"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { buildCitation, type Rec } from "../lib/record";
import styles from "./Provenance.module.css";

/* Layer 5 — Source (where the record came from) · Citation (cite this object) ·
   Provenance (what MGDA did with it). Kept as three distinct blocks. On the dark
   editorial band (layout 5) the wrapper sets --block-* theme vars; the classes
   here read them with cream-ground fallbacks. */

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const t = useRef<number | null>(null);
  useEffect(() => () => {
    if (t.current) window.clearTimeout(t.current);
  }, []);
  return (
    <button
      type="button"
      className={styles.copyBtn}
      data-copied={copied || undefined}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          if (t.current) window.clearTimeout(t.current);
          t.current = window.setTimeout(() => setCopied(false), 1800);
        } catch {
          /* text is selectable on the page */
        }
      }}
    >
      {copied ? "Copied" : "Copy citation"}
    </button>
  );
}

export function SourceBlock({ rec }: { rec: Rec }) {
  return (
    <div className={styles.block}>
      <p className={styles.blockHead}>Source</p>
      <p className={styles.blockNote}>Where this record came from.</p>
      <dl className={styles.kv}>
        <div>
          <dt>Source institution</dt>
          <dd>{rec.sourceRecord.institution}</dd>
        </div>
        <div>
          <dt>Original record</dt>
          <dd>
            {rec.sourceRecord.recordTitle}
            {rec.sourceRecord.recordHref ? (
              <>
                {" "}
                <a
                  className={styles.srcLink}
                  href={rec.sourceRecord.recordHref}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open <ArrowUpRight size={13} strokeWidth={3} aria-hidden="true" />
                </a>
              </>
            ) : null}
          </dd>
        </div>
        <div>
          <dt>Access</dt>
          <dd>{rec.sourceRecord.accessedText}</dd>
        </div>
      </dl>
    </div>
  );
}

export function CitationBlock({ rec }: { rec: Rec }) {
  const cite = buildCitation(rec);
  return (
    <div className={styles.block}>
      <p className={styles.blockHead}>Cite this object</p>
      <p className={styles.blockNote}>A citation for this object record.</p>
      <p className={styles.citeText}>{cite}</p>
      {rec.citation ? (
        <p className={styles.citeText}>
          Source citation (as provided): {rec.citation.label}
        </p>
      ) : null}
      <div className={styles.copyRow}>
        <CopyButton text={cite} />
      </div>
      <p className={styles.aboutNote}>
        Cites the object record. To cite the whole archive, see{" "}
        <a href="/about#cite">About</a>.
      </p>
    </div>
  );
}

export function ProvenanceBlock({ rec }: { rec: Rec }) {
  return (
    <div className={styles.block}>
      <p className={styles.blockHead}>Provenance</p>
      <p className={styles.blockNote}>What MGDA did with this record.</p>
      <dl className={styles.kv}>
        <div>
          <dt>Record status</dt>
          <dd>{rec.provenance.recordStatus}</dd>
        </div>
        <div>
          <dt>Release</dt>
          <dd>{rec.provenance.releaseLabel}</dd>
        </div>
        <div>
          <dt>Source verification</dt>
          <dd>{rec.provenance.sourceVerification}</dd>
        </div>
        <div>
          <dt>Last verified</dt>
          <dd>{rec.provenance.lastVerified}</dd>
        </div>
      </dl>
      <a className={styles.foldLink} href="/source#version">
        Full technical identity — Source
      </a>
    </div>
  );
}

export function FootTriple({ rec }: { rec: Rec }) {
  return (
    <div className={styles.foot} data-cols="3">
      <SourceBlock rec={rec} />
      <CitationBlock rec={rec} />
      <ProvenanceBlock rec={rec} />
    </div>
  );
}
