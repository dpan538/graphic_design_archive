"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { ArrowUpRight } from "lucide-react";
import { buildCitation, type Rec } from "../lib/record";
import styles from "./MobileProvenance.module.css";

function Fold({ label, children }: { label: string; children: ReactNode }) {
  return (
    <details className={styles.fold}>
      <summary>{label}</summary>
      <div className={styles.foldBody}>{children}</div>
    </details>
  );
}

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

/* Layer 5, mobile — three blocks; non-essential detail folded by default. */
export default function MobileProvenance({ rec }: { rec: Rec }) {
  const cite = buildCitation(rec);

  return (
    <div className={styles.wrap}>
      <div className={styles.block}>
        <p className={styles.head}>Source</p>
        <p className={styles.note}>Where this record came from.</p>
        <Fold label="Source details">
          <dl className={styles.kv}>
            <div>
              <dt>Source institution</dt>
              <dd>{rec.sourceRecord.institution}</dd>
            </div>
            <div>
              <dt>Original record</dt>
              <dd>
                {rec.sourceRecord.recordTitle}{" "}
                {rec.sourceRecord.recordHref ? (
                  <a
                    className={styles.srcLink}
                    href={rec.sourceRecord.recordHref}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open <ArrowUpRight size={13} strokeWidth={3} aria-hidden="true" />
                  </a>
                ) : null}
              </dd>
            </div>
            <div>
              <dt>Access</dt>
              <dd>{rec.sourceRecord.accessedText}</dd>
            </div>
          </dl>
        </Fold>
      </div>

      <div className={styles.block}>
        <p className={styles.head}>Cite this object</p>
        <p className={styles.note}>A citation for this object record.</p>
        <div className={styles.copyRow}>
          <CopyButton text={cite} />
        </div>
        <Fold label="Citation text">
          <p className={styles.citeText}>{cite}</p>
          {rec.citation ? (
            <p className={styles.citeText}>
              Source citation (as provided): {rec.citation.label}
            </p>
          ) : null}
        </Fold>
        <p className={styles.aboutNote}>
          Cites the object record. To cite the whole archive, see{" "}
          <a href="/about#cite">About</a>.
        </p>
      </div>

      <div className={styles.block}>
        <p className={styles.head}>Provenance</p>
        <p className={styles.note}>What MGDA did with this record.</p>
        <Fold label="Provenance details">
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
        </Fold>
        <a className={styles.foldLink} href="/source#version">
          Full technical identity — Source
        </a>
      </div>
    </div>
  );
}
