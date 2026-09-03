import { rowsFor, type LayoutId, type Rec } from "../lib/record";
import { fitProfile } from "../lib/fitLayout";
import VisualRecord from "./VisualRecord";
import { Classification, MetaPairs } from "./CatalogueMetadata";
import Ledger from "./Ledger";
import DescriptionBlock from "./DescriptionBlock";
import {
  CitationBlock,
  FootTriple,
  ProvenanceBlock,
  SourceBlock,
} from "./Provenance";
import styles from "./ObjectRecord.module.css";

type Props = {
  rec: Rec;
  layout: LayoutId;
  /* a record-only entry: retained for catalogue and provenance, not a
     reader-facing object — no visual or descriptive layers */
  recordOnly?: boolean;
};

/* ---------------------------------------------------------------- Scaffolding */

function Eyebrow({ recordOnly }: { recordOnly?: boolean }) {
  return <span className={styles.recEyebrow}>{recordOnly ? "Archive record" : "MGDA record"}</span>;
}

/* the record-only notice: says plainly what this page is */
function RecordNotice() {
  return (
    <p className={styles.recordNotice}>
      This record is retained for catalogue and provenance purposes. No reader-facing visual or descriptive
      object content is currently available, and it is not listed in the Index. Its identity, source,
      citation and provenance stand.
    </p>
  );
}

function Title({ text }: { text: string }) {
  return <h1 className={styles.title}>{text}</h1>;
}

function IdentLine({ rec }: { rec: Rec }) {
  const parts = [rec.surfaceId, rec.typeLabel, rec.displayDate, rec.placeLabel].filter(
    Boolean,
  );
  return (
    <p className={styles.identLine}>
      {parts.map((p, i) => (
        <span key={p}>
          {i > 0 ? <span className={styles.sep}>·</span> : null}
          {p}
        </span>
      ))}
    </p>
  );
}

function Header({ rec, recordOnly }: { rec: Rec; recordOnly?: boolean }) {
  return (
    <div className={styles.header}>
      <Eyebrow recordOnly={recordOnly} />
      <Title text={rec.title} />
      <IdentLine rec={rec} />
      {recordOnly ? <RecordNotice /> : null}
    </div>
  );
}

function LayerHead({ n, name, tone }: { n: string; name: string; tone: string }) {
  return (
    <div
      className={styles.layerHead}
      style={{ ["--lc" as string]: `var(--l-${tone})` }}
    >
      <span className={styles.layerNum}>{n}</span>
      <span className={styles.layerName}>{name}</span>
    </div>
  );
}

/* ---------------------------------------------------------------- Layouts */

export default function ObjectRecord({
  rec,
  layout,
  recordOnly = false,
}: Props) {
  const desc = recordOnly ? null : rec.description;
  const { identity, classification, source } = rowsFor(rec);
  // Column counts follow the record's content volume, not the layout.
  const { metaCols, proseCols } = fitProfile(rec, desc);

  const visual = recordOnly ? null : (
    <div className={styles.vbWrap}>
      <VisualRecord rec={rec} />
    </div>
  );

  const metaSection = (
    <section className={styles.sec}>
      <LayerHead n="03" name="Catalogue metadata" tone="meta" />
      <div className={styles.mt}>
        <MetaPairs rec={rec} cols={metaCols} />
      </div>
      <div className={styles.mt}>
        <Classification rec={rec} cols={metaCols} />
      </div>
    </section>
  );

  const descSection = desc ? (
    <section className={styles.sec}>
      <LayerHead n="04" name="Description" tone="desc" />
      <div className={styles.mt}>
        <DescriptionBlock text={desc} cols={proseCols} />
      </div>
    </section>
  ) : null;

  const footSection = (
    <section className={styles.sec}>
      <LayerHead n="05" name="Source · Citation · Provenance" tone="src" />
      <div className={styles.mt}>
        <FootTriple rec={rec} />
      </div>
    </section>
  );

  /* 1 — Catalogue entry */
  if (layout === 1) {
    return (
      <div className={styles.record} data-layout="1">
        <div className={styles.inner}>
          <Header rec={rec} recordOnly={recordOnly} />
          {visual}
          {metaSection}
          {descSection}
          {footSection}
        </div>
      </div>
    );
  }

  /* 2 — Tabular */
  if (layout === 2) {
    return (
      <div className={styles.record} data-layout="2">
        <div className={styles.inner}>
          <Header rec={rec} recordOnly={recordOnly} />
          {visual}
          <section className={styles.sec}>
            <LayerHead n="03" name="Catalogue metadata" tone="meta" />
            <Ledger
              groups={[
                { title: "Identity", rows: identity },
                { title: "Classification", rows: classification },
              ]}
            />
          </section>
          {descSection}
          {footSection}
        </div>
      </div>
    );
  }

  /* 3 — Ledger (whole record) */
  if (layout === 3) {
    return (
      <div className={styles.record} data-layout="3">
        <div className={styles.inner}>
          <Header rec={rec} recordOnly={recordOnly} />
          {visual}
          <Ledger
            groups={[
              { title: "Object identity & metadata", rows: identity },
              { title: "Classification", rows: classification },
              { title: "Source & provenance", rows: source },
            ]}
          />
          {desc ? (
            <section className={styles.sec}>
              <LayerHead n="04" name="Description" tone="desc" />
              <div className={styles.mt}>
                <DescriptionBlock text={desc} cols={proseCols} />
              </div>
            </section>
          ) : null}
          <section className={styles.sec}>
            <CitationBlock rec={rec} />
          </section>
        </div>
      </div>
    );
  }

  /* 4 — Reading-led (description first) */
  if (layout === 4) {
    return (
      <div className={styles.record} data-layout="4">
        <div className={styles.inner}>
          <Header rec={rec} recordOnly={recordOnly} />
          {visual}
          {descSection}
          {metaSection}
          {footSection}
        </div>
      </div>
    );
  }

  /* 5 — Editorial spread (full-width headline + dark foot band) */
  return (
    <div className={styles.record} data-layout="5">
      <div className={styles.spreadHead}>
        <Eyebrow recordOnly={recordOnly} />
        <Title text={rec.title} />
        <div className={styles.rule5} />
      </div>
      <div className={styles.inner}>
        <IdentLine rec={rec} />
        {visual}
        {metaSection}
        {descSection}
      </div>
      <div className={styles.footBand}>
        <div className={styles.footInner}>
          <SourceBlock rec={rec} />
          <CitationBlock rec={rec} />
          <ProvenanceBlock rec={rec} />
        </div>
      </div>
    </div>
  );
}
