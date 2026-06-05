"use client";

import type { Surface, SurfaceImage, TableKind } from "@/types/archive";
import { getSurface, getSurfaces } from "@/lib/archive-data";
import {
  selectTextPageLayout,
  type TextPageLayoutId,
} from "@/lib/text-page-layout";
import { useState } from "react";

interface TextPageProps {
  id: TextPageLayoutId;
  surface: Surface;
}

function mustSurface(id: string): Surface {
  const surface = getSurface(id);
  if (!surface) throw new Error(`Missing text-page test surface: ${id}`);
  return surface;
}

function sampleSurface(
  predicate: (surface: Surface) => boolean,
  fallbackId = "SURF-ER1830R016",
): Surface {
  return getSurfaces().find(predicate) ?? mustSurface(fallbackId);
}

function surfaceTextLength(surface: Surface): number {
  if (surface.readingTextLength) return surface.readingTextLength;
  return clean(
    [
      surface.descriptionSummary,
      surface.sourceDescription,
      surface.historicalContextNote,
      surface.classificationRationale,
      surface.uncertaintyNote,
      surface.citationBasis,
    ]
      .filter(Boolean)
      .join(" "),
  ).length;
}

function clean(text: string | null | undefined): string {
  return (
    text
      ?.replace(/\\n/g, " ")
      .replace(/\s+/g, " ")
      .trim() || "unrecorded"
  );
}

function sentenceSplit(text: string | null | undefined): string[] {
  return clean(text)
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function clipWords(text: string | null | undefined, maxWords = 18): string {
  return clean(text).split(" ").slice(0, maxWords).join(" ");
}

function pickSentences(
  text: string | null | undefined,
  maxChars: number,
  maxSentences = 2,
): string {
  const sentences = sentenceSplit(text);
  if (sentences.length === 0) {
    return clipWords(text, Math.max(12, Math.floor(maxChars / 7)));
  }
  const selected: string[] = [];
  let total = 0;
  for (const sentence of sentences) {
    const next = total + sentence.length + (selected.length ? 1 : 0);
    if (selected.length > 0 && next > maxChars) break;
    selected.push(sentence);
    total = next;
    if (selected.length >= maxSentences) break;
  }
  return selected.join(" ");
}

function displayDate(surface: Surface): string {
  return clean(surface.dateText).replace(/T00:00:00Z$/i, "");
}

function displayId(surface: Surface): string {
  return surface.sourceRecordId.replace(/^REC-/, "");
}

function folderLine(surface: Surface): string {
  return surface.folders.map((folder) => folder.title).join(" / ");
}

function tableRows(
  surface: Surface,
  kind: TableKind,
  maxRows = 4,
): Array<[string, string]> {
  const table = surface.tables.find((entry) => entry.kind === kind);
  return table?.rows.slice(0, maxRows) ?? [];
}

function packet(surface: Surface) {
  const lead = pickSentences(
    surface.descriptionSummary || surface.sourceDescription,
    300,
    3,
  );
  const detail = pickSentences(
    surface.sourceDescription || surface.descriptionSummary,
    420,
    4,
  );
  const context = pickSentences(surface.historicalContextNote, 300, 3);
  const rationale = pickSentences(surface.classificationRationale, 220, 2);
  const notes = pickSentences(surface.sourceNotes, 240, 2);
  const citation = pickSentences(surface.citationBasis, 220, 2);
  const pull = clipWords(
    surface.descriptionSummary ||
      surface.sourceDescription ||
      surface.historicalContextNote,
    28,
  );
  return { lead, detail, context, rationale, notes, citation, pull };
}

function textBlocks(surface: Surface, maxBlocks = 5, maxChars = 420): string[] {
  const fields = [
    surface.sourceDescription,
    surface.descriptionSummary,
    surface.historicalContextNote,
    surface.classificationRationale,
    surface.sourceNotes,
    surface.citationBasis,
    surface.sourceSubjects,
  ];
  const blocks: string[] = [];
  for (const field of fields) {
    const value = pickSentences(field, maxChars, 4);
    if (value && value !== "unrecorded" && !blocks.includes(value)) {
      blocks.push(value);
    }
    if (blocks.length >= maxBlocks) break;
  }
  return blocks;
}

function archiveBlocks(surface: Surface, maxBlocks = 8, maxChars = 360): string[] {
  const metadata = [
    `Provider: ${surface.sourceName}. Date span: ${displayDate(surface)}. Type: ${surface.objectType}. Creator: ${surface.creator || "Unknown"}.`,
    `Folder path: ${folderLine(surface)}.`,
    surface.sourceSubjects ? `Source subjects: ${clean(surface.sourceSubjects)}.` : "",
  ];
  const fields = [
    surface.sourceDescription,
    surface.descriptionSummary,
    surface.historicalContextNote,
    surface.classificationRationale,
    surface.sourceNotes,
    surface.citationBasis,
    ...metadata,
  ];
  const blocks: string[] = [];
  for (const field of fields) {
    const value = pickSentences(field, maxChars, 4);
    if (value && value !== "unrecorded" && !blocks.includes(value)) {
      blocks.push(value);
    }
    if (blocks.length >= maxBlocks) break;
  }
  return blocks;
}

function textPageTitle(surface: Surface): string {
  return clean(surface.title)
    .replace(" - international pdf magazine of graphics arts", "")
    .replace("Welcome to the Australian Institute of Aboriginal and Torres Strait Islander Studies ", "")
    .replace(" : ", ": ");
}

function renderableImages(surface: Surface): SurfaceImage[] {
  const seen = new Set<string>();
  return [surface.image, ...(surface.images ?? [])].filter((image) => {
    if (!image.url || !["IMG01", "IMG02", "IMG03"].includes(image.state)) return false;
    if (seen.has(image.url)) return false;
    seen.add(image.url);
    return true;
  });
}

function ImagePlate({
  image,
  title,
  position = "center center",
  className = "",
  label,
  fit = "cover",
}: {
  image: SurfaceImage;
  title: string;
  position?: string;
  className?: string;
  label?: string;
  fit?: "cover" | "contain";
}) {
  const [failed, setFailed] = useState(false);
  if (!image.url || failed) {
    return (
      <figure className={`text-page__crop text-page__crop--fallback ${className}`}>
        <div className="text-page__crop-fallback-copy">
          <span>{label || image.state}</span>
          <strong>{title}</strong>
          <small>{image.credit || "source image withheld"}</small>
        </div>
      </figure>
    );
  }
  return (
    <figure
      className={`text-page__crop ${
        fit === "contain" ? "text-page__crop--contain" : ""
      } ${className}`}
    >
      <img
        src={image.url}
        alt={title}
        loading="eager"
        style={{ objectPosition: position, objectFit: fit }}
        onError={() => setFailed(true)}
      />
      {label ? <figcaption>{label}</figcaption> : null}
    </figure>
  );
}

function Crop({
  surface,
  position = "center center",
  className = "",
  label,
  fit = "cover",
}: {
  surface: Surface;
  position?: string;
  className?: string;
  label?: string;
  fit?: "cover" | "contain";
}) {
  return (
    <ImagePlate
      image={surface.image}
      title={surface.title}
      position={position}
      className={className}
      label={label}
      fit={fit}
    />
  );
}

function MetaBar({
  left,
  center,
  right,
}: {
  left: string;
  center?: string;
  right: string;
}) {
  return (
    <div className="text-page__meta-line">
      <span>{left}</span>
      {center ? <span>{center}</span> : <span />}
      <span>{right}</span>
    </div>
  );
}

function Module({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <section className="text-page__module">
      <span className="text-page__label">{label}</span>
      <div>{children}</div>
    </section>
  );
}

function RowList({
  rows,
  className = "",
}: {
  rows: Array<[string, string]>;
  className?: string;
}) {
  return (
    <dl className={`text-page__row-list ${className}`}>
      {rows.map(([label, value]) => (
        <div key={`${label}-${value}`}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function TP01FragmentField({ surface, id }: TextPageProps) {
  const text = packet(surface);
  const lead = pickSentences(surface.descriptionSummary || surface.sourceDescription, 170, 2);
  const context = pickSentences(surface.historicalContextNote, 150, 1);
  const caption = pickSentences(surface.sourceDescription || surface.descriptionSummary, 135, 1);
  return (
    <article className="text-page text-page--v-fragment">
      <MetaBar left={displayDate(surface)} center={surface.sourceName} right={id} />
      <blockquote className="text-page__display-quote">“{text.pull}”</blockquote>
      <div className="text-page__fragment-lower">
        <div className="text-page__fragment-copy">
          <Module label="source text">
            <p>{lead}</p>
          </Module>
          <Module label="context">
            <p>{context}</p>
          </Module>
        </div>
        <div className="text-page__fragment-visual">
          <Crop surface={surface} position="center 26%" label={surface.sourceName} />
          <p className="text-page__caption-block">{caption}</p>
        </div>
      </div>
      <footer className="text-page__footer-line">
        <span>{folderLine(surface)}</span>
        <span>{displayId(surface)}</span>
      </footer>
    </article>
  );
}

function TP02RadicalInset({ surface, id }: TextPageProps) {
  const text = packet(surface);
  const context = pickSentences(surface.historicalContextNote, 190, 2);
  const description = pickSentences(surface.descriptionSummary, 190, 2);
  const classification = pickSentences(surface.classificationRationale, 150, 1);
  return (
    <article className="text-page text-page--v-radical">
      <div className="text-page__radical-top">
        <p>{context}</p>
        <h2>{surface.title}</h2>
      </div>
      <div className="text-page__radical-middle">
        <Crop surface={surface} position="center 20%" label={displayDate(surface)} />
        <div className="text-page__radical-stack">
          <Module label="description">
            <p>{description}</p>
          </Module>
          <Module label="classification">
            <p>{classification}</p>
          </Module>
        </div>
      </div>
      <footer className="text-page__footer-line">
        <span>{surface.sourceName}</span>
        <span>{id}</span>
      </footer>
    </article>
  );
}

function TP03EditorialColumn({ surface, id }: TextPageProps) {
  const text = packet(surface);
  const blocks = archiveBlocks(surface, 5, 250);
  return (
    <article className="text-page text-page--v-editorial-column">
      <div className="text-page__editorial-top">
        <span>{surface.creator || surface.sourceName}</span>
        <span>{displayId(surface)}</span>
      </div>
      <div className="text-page__editorial-body">
        <div className="text-page__editorial-left">
          <span>{displayDate(surface)}</span>
          <strong>{surface.objectType}</strong>
          <small>{folderLine(surface)}</small>
        </div>
        <div className="text-page__editorial-right">
          <h2>{surface.title}</h2>
          <div className="text-page__editorial-image-stack">
            <Crop surface={surface} position="center center" label="source frame" fit="contain" />
            <Crop surface={surface} position="center 18%" label="upper evidence" />
            <Crop surface={surface} position="center 72%" label="lower evidence" />
          </div>
          <p>{blocks[0] || text.detail}</p>
          <p>{blocks[1] || text.context}</p>
          <p>{blocks[2] || text.rationale}</p>
        </div>
      </div>
      <footer className="text-page__footer-line">
        <span>{displayDate(surface)}</span>
        <span>{id}</span>
      </footer>
    </article>
  );
}

function TP04EssayChorus({ surface, id }: TextPageProps) {
  const text = packet(surface);
  const blocks = archiveBlocks(surface, 6, 220);
  return (
    <article className="text-page text-page--v-essay-chorus">
      <MetaBar left={surface.sourceName} center={displayDate(surface)} right={id} />
      <div className="text-page__chorus-header">
        <h2>{textPageTitle(surface)}</h2>
        <p>{blocks[0] || text.lead}</p>
      </div>
      <div className="text-page__chorus-images">
        <Crop surface={surface} position="center center" label="original record image" fit="contain" />
        <Crop surface={surface} position="left center" label="left plate crop" />
        <Crop surface={surface} position="right center" label="right plate crop" />
      </div>
      <div className="text-page__chorus-grid">
        <p>{blocks[1] || text.context}</p>
        <p>{blocks[2] || text.detail}</p>
        <p>{blocks[3] || text.rationale}</p>
      </div>
      <footer className="text-page__footer-line">
        <span>{folderLine(surface)}</span>
        <span>{displayId(surface)}</span>
      </footer>
    </article>
  );
}

function TP05AnnotationGrid({ surface, id }: TextPageProps) {
  const text = packet(surface);
  const blocks = archiveBlocks(surface, 4, 230);
  return (
    <article className="text-page text-page--v-annotation-grid">
      <div className="text-page__annotation-head">
        <span>{id}</span>
        <h2>{textPageTitle(surface)}</h2>
      </div>
      <Crop
        surface={surface}
        position="center center"
        label="source image, uncropped"
        fit="contain"
        className="text-page__annotation-main-image"
      />
      <div className="text-page__annotation-layout">
        <Module label="archive note">
          <p>{blocks[0] || text.rationale || text.notes}</p>
        </Module>
        <Module label="source return">
          <p>{blocks[1] || text.detail}</p>
        </Module>
        <Module label="context">
          <p>{blocks[2] || text.context}</p>
        </Module>
      </div>
      <footer className="text-page__footer-line">
        <span>{surface.sourceName}</span>
        <span>{displayDate(surface)}</span>
      </footer>
    </article>
  );
}

function TP06SpreadCover({ surface, id }: TextPageProps) {
  const blocks = archiveBlocks(surface, 7, 220);
  return (
    <article className="text-page text-page--v-spread-cover">
      <div className="text-page__spread-cover-grid">
        <div className="text-page__spread-cover-title">
          <span>{surface.sourceName}</span>
          <h2>{textPageTitle(surface)}</h2>
        </div>
        <p>{blocks[0]}</p>
        <p>{blocks[1]}</p>
        <p>{blocks[2]}</p>
        <p>{blocks[3]}</p>
        <p>{blocks[4]}</p>
        <div>
          <small>{displayDate(surface)}</small>
          <strong>06</strong>
        </div>
      </div>
      <footer className="text-page__footer-line">
        <span>{id}</span>
        <span>{folderLine(surface)}</span>
      </footer>
    </article>
  );
}

function TP07SpreadEssay({ surface, id }: TextPageProps) {
  const blocks = archiveBlocks(surface, 8, 240);
  return (
    <article className="text-page text-page--v-spread-essay">
      <div className="text-page__spread-page-no">45</div>
      <div className="text-page__spread-essay-head">
        <small>{surface.creator || surface.sourceName}</small>
        <h2>{textPageTitle(surface)}</h2>
      </div>
      <div className="text-page__spread-essay-body">
        {blocks.slice(0, 8).map((block, index) => (
          <p key={index}>{block}</p>
        ))}
      </div>
      <footer className="text-page__footer-line">
        <span>{displayDate(surface)}</span>
        <span>{id}</span>
      </footer>
    </article>
  );
}

function TP08SpreadQuote({ surface, id }: TextPageProps) {
  const text = packet(surface);
  const blocks = archiveBlocks(surface, 7, 190);
  const rows = [
    ["SRC", surface.sourceName, blocks[0] || text.detail],
    ["OBJ", surface.objectType, blocks[1] || text.context],
    ["CTX", displayDate(surface), blocks[2] || text.rationale],
    ["CLS", folderLine(surface), blocks[3] || text.notes],
    ["CIT", displayId(surface), blocks[4] || text.citation],
  ];
  return (
    <article className="text-page text-page--v-spread-quote text-page--v-transcript">
      <div className="text-page__transcript-leaf">
        <div className="text-page__transcript-head">
          <small>{id}</small>
          <strong>62</strong>
        </div>
        <div className="text-page__transcript-intro">
          <span>{surface.sourceName}</span>
          <h2>{textPageTitle(surface)}</h2>
          <p>{text.pull}</p>
        </div>
        <div className="text-page__transcript-rule" />
        <div className="text-page__transcript-rows">
          {rows.map(([label, meta, body]) => (
            <div key={label}>
              <span>{label}</span>
              <small>{meta}</small>
              <p>{body}</p>
            </div>
          ))}
        </div>
        <p className="text-page__transcript-pull">
          {blocks[5] || blocks[0] || text.context}
        </p>
      </div>
      <footer className="text-page__footer-line">
        <span>{displayDate(surface)}</span>
        <span>source interview leaf</span>
      </footer>
    </article>
  );
}

function TP09SpreadBody({ surface, id }: TextPageProps) {
  const blocks = archiveBlocks(surface, 5, 130);
  const titleParts = textPageTitle(surface).split(/\s+/).filter(Boolean);
  const contents = [
    ["01", "source record", surface.sourceName, blocks[0]],
    ["02", "object condition", surface.objectType, blocks[1]],
    ["03", "classification", folderLine(surface), blocks[2]],
    ["04", "citation basis", displayId(surface), blocks[3]],
    ["05", "archive note", displayDate(surface), blocks[4]],
  ];
  const visibleContents = contents.slice(0, 4);
  return (
    <article className="text-page text-page--v-spread-body text-page--v-index-leaf">
      <div className="text-page__contents-leaf">
        <div className="text-page__contents-head">
          <span>{id}</span>
          <strong>63</strong>
        </div>
        <div className="text-page__contents-title">
          <span>{titleParts.slice(0, 3).join(" ")}</span>
          <h2>{titleParts.slice(3).join(" ") || textPageTitle(surface)}</h2>
          <p>{blocks[5] || blocks[0]}</p>
        </div>
        <div className="text-page__contents-grid">
          <div className="text-page__contents-index">
            {visibleContents.map(([number, label, meta, body]) => (
              <section key={number}>
                <span>{number}</span>
                <h3>{label}</h3>
                <small>{meta}</small>
                <p>{body}</p>
              </section>
            ))}
          </div>
          <div className="text-page__contents-manifest">
            {titleParts.slice(0, 9).map((part, index) => (
              <span key={`${part}-${index}`}>{part}</span>
            ))}
          </div>
        </div>
      </div>
      <footer className="text-page__footer-line">
        <span>{surface.sourceName}</span>
        <span>contents / body leaf</span>
      </footer>
    </article>
  );
}

function TP10GeologyLedger({ surface, id }: TextPageProps) {
  const text = packet(surface);
  const blocks = archiveBlocks(surface, 5, 270);
  return (
    <article className="text-page text-page--h-geology-ledger">
      <div className="text-page__geology-left">
        <Crop surface={surface} position="center 20%" label={surface.sourceName} fit="contain" />
        <p>{blocks[2] || text.rationale}</p>
      </div>
      <div className="text-page__geology-right">
        <div className="text-page__geology-topline">
          <span>{displayDate(surface)}</span>
          <span>{id}</span>
        </div>
        <h2>{surface.title}</h2>
        <Module label="source note">
          <p>{blocks[0] || text.lead}</p>
        </Module>
        <Module label="archive note">
          <p>{blocks[1] || text.context || text.rationale}</p>
        </Module>
        <Module label="classification">
          <p>{blocks[2] || text.rationale}</p>
        </Module>
        <Module label="citation">
          <p>{blocks[3] || text.citation}</p>
        </Module>
        <div className="text-page__geology-foot">
          <span>{folderLine(surface)}</span>
          <span>{displayId(surface)}</span>
        </div>
      </div>
    </article>
  );
}

function TP11FreeHorizon({ surface, id }: TextPageProps) {
  const text = packet(surface);
  const blocks = archiveBlocks(surface, 10, 300);
  return (
    <article className="text-page text-page--h-free-horizon">
      <MetaBar left={surface.sourceName} center={displayDate(surface)} right={id} />
      <div className="text-page__free-horizon-body">
        <div className="text-page__free-horizon-center">
          <h2>{surface.title}</h2>
          <p>{text.pull}</p>
          <p>{blocks[0] || text.lead}</p>
          <p>{blocks[1] || text.detail}</p>
        </div>
        <div className="text-page__free-horizon-text">
          {blocks.slice(2, 6).map((block, index) => (
            <p key={index}>{block}</p>
          ))}
        </div>
        <div className="text-page__free-horizon-right">
          {blocks.slice(6, 10).map((block, index) => (
            <p key={index}>{block}</p>
          ))}
        </div>
      </div>
      <footer className="text-page__footer-line">
        <span>{folderLine(surface)}</span>
        <span>{displayId(surface)}</span>
      </footer>
    </article>
  );
}

function TP12PerforatedField({ surface, id }: TextPageProps) {
  const text = packet(surface);
  const blocks = archiveBlocks(surface, 5, 150);
  return (
    <article className="text-page text-page--v-perforated-field">
      <div className="text-page__perf-grid">
        <section>
          <span>topic</span>
          <h2>{textPageTitle(surface)}</h2>
          <p>{text.pull}</p>
        </section>
        <section>
          <span>source</span>
          <strong>{surface.sourceName}</strong>
          <p>{blocks[0]}</p>
        </section>
        <section className="text-page__perf-vertical">
          <span>opening</span>
          <strong>{displayDate(surface)}</strong>
        </section>
        <section>
          <span>context</span>
          <p>{blocks[1] || text.context}</p>
        </section>
        <section>
          <span>classification</span>
          <p>{folderLine(surface)}</p>
        </section>
        <section className="text-page__perf-address">
          <span>archive address</span>
          <p>{blocks[2] || text.rationale}</p>
        </section>
      </div>
      <footer className="text-page__footer-line">
        <span>{id}</span>
        <span>{displayId(surface)}</span>
      </footer>
    </article>
  );
}

function TP13TabbedRegister({ surface, id }: TextPageProps) {
  const blocks = archiveBlocks(surface, 6, 190);
  return (
    <article className="text-page text-page--v-marginal-essay">
      <MetaBar left={id} center={surface.sourceName} right={displayDate(surface)} />
      <div className="text-page__marginal-title">
        <span>{displayId(surface)}</span>
        <h2>{textPageTitle(surface)}</h2>
      </div>
      <div className="text-page__marginal-body">
        <aside>
          <strong>01</strong>
          <span>{surface.objectType}</span>
          <span>{folderLine(surface)}</span>
        </aside>
        <p>{blocks[0]}</p>
        <p>{blocks[1]}</p>
        <blockquote>{blocks[2] || blocks[0]}</blockquote>
      </div>
      <footer className="text-page__marginal-footer">
        <p>{blocks[3] || surface.citationBasis}</p>
        <span>{surface.image.state} / {surface.rights.label}</span>
      </footer>
    </article>
  );
}

function TP14WaitingPlate({ surface, id }: TextPageProps) {
  const blocks = archiveBlocks(surface, 6, 185);
  return (
    <article className="text-page text-page--v-waiting-plate">
      <div className="text-page__waiting-top">
        <p>{blocks[0]}</p>
        <Crop surface={surface} position="center center" fit="contain" label={surface.sourceName} />
      </div>
      <div className="text-page__waiting-body">
        <p>{blocks[1]}</p>
        <p>{blocks[2]}</p>
      </div>
      <div className="text-page__waiting-title">
        <h2>{textPageTitle(surface)}</h2>
        <span>{displayDate(surface)}</span>
      </div>
      <footer className="text-page__footer-line">
        <span>{id}</span>
        <span>{displayId(surface)}</span>
      </footer>
    </article>
  );
}

function TP15OverprintWindow({ surface, id }: TextPageProps) {
  const blocks = archiveBlocks(surface, 7, 160);
  return (
    <article className="text-page text-page--v-cutline-plate">
      <header>
        <span>{id}</span>
        <strong>{displayDate(surface)}</strong>
      </header>
      <div className="text-page__cutline-main">
        <div className="text-page__cutline-copy">
          <h2>{textPageTitle(surface)}</h2>
          <p>{blocks[0]}</p>
          <p>{blocks[1]}</p>
        </div>
        <Crop surface={surface} position="center center" fit="contain" label={surface.image.state} />
      </div>
      <div className="text-page__cutline-band">
        <p>{blocks[2]}</p>
        <p>{blocks[3] || surface.citationBasis}</p>
        <p>{blocks[4] || folderLine(surface)}</p>
      </div>
      <footer className="text-page__footer-line">
        <span>{surface.sourceName}</span>
        <span>{displayId(surface)}</span>
      </footer>
    </article>
  );
}

function TP16SpecimenWall({ surface, id }: TextPageProps) {
  const blocks = archiveBlocks(surface, 7, 150);
  const plates = renderableImages(surface);
  const hasImageSet = plates.length >= 3;
  return (
    <article className="text-page text-page--v-source-dossier">
      <header>
        <span>{displayId(surface)}</span>
        <h2>{textPageTitle(surface)}</h2>
      </header>
      <div className="text-page__source-dossier-grid">
        <div className="text-page__source-dossier-copy">
          {blocks.slice(0, 4).map((block, index) => (
            <p key={index}>{block}</p>
          ))}
        </div>
        <div className={hasImageSet ? "text-page__source-dossier-plates" : "text-page__source-dossier-single"}>
          {hasImageSet ? (
            plates.slice(0, 4).map((image, index) => (
              <ImagePlate
                key={image.url || index}
                image={image}
                title={surface.title}
                fit="contain"
                label={`F${String(index + 1).padStart(2, "0")}`}
              />
            ))
          ) : (
            <Crop surface={surface} position="center center" fit="contain" label={surface.image.state} />
          )}
        </div>
      </div>
      <div className="text-page__source-dossier-register">
        <span>{surface.sourceName}</span>
        <span>{surface.objectType}</span>
        <span>{folderLine(surface)}</span>
      </div>
      <footer className="text-page__footer-line">
        <span>{displayDate(surface)}</span>
        <span>{id}</span>
      </footer>
    </article>
  );
}

function TP17FactoryCard({ surface, id }: TextPageProps) {
  const blocks = archiveBlocks(surface, 6, 190);
  return (
    <article className="text-page text-page--h-factory-card">
      <div className="text-page__factory-image">
        <Crop surface={surface} position="center center" fit="contain" />
        <span>{surface.sourceName}</span>
      </div>
      <div className="text-page__factory-copy">
        <MetaBar left="02" center={id} right={displayDate(surface)} />
        <h2>{textPageTitle(surface)}</h2>
        <p className="text-page__factory-lead">{blocks[0]}</p>
        <div className="text-page__factory-grid">
          {blocks.slice(1, 5).map((block, index) => (
            <p key={index}>{block}</p>
          ))}
        </div>
        <footer>
          <span>{folderLine(surface)}</span>
          <span>{displayId(surface)}</span>
        </footer>
      </div>
    </article>
  );
}

function TP18ScheduleLedger({ surface, id }: TextPageProps) {
  const blocks = archiveBlocks(surface, 8, 115);
  const rows = [
    ["provider", surface.sourceName, blocks[0]],
    ["date", displayDate(surface), blocks[1]],
    ["type", surface.objectType, blocks[2]],
    ["record", displayId(surface), blocks[3]],
    ["folder", folderLine(surface), blocks[4]],
    ["citation", "source basis", blocks[5]],
  ];
  return (
    <article className="text-page text-page--h-schedule-ledger">
      <div className="text-page__schedule-title">
        <span>{displayDate(surface)}</span>
        <h2>{textPageTitle(surface)}</h2>
        <p>{clipWords(surface.descriptionSummary || surface.sourceDescription, 20)}</p>
      </div>
      <div className="text-page__schedule-rows">
        {rows.map(([label, meta, body]) => (
          <section key={label}>
            <span>{label}</span>
            <strong>{meta}</strong>
            <p>{body}</p>
          </section>
        ))}
      </div>
      <footer className="text-page__footer-line">
        <span>{id}</span>
        <span>{surface.sourceName}</span>
      </footer>
    </article>
  );
}

export function TextPageLayout(props: TextPageProps) {
  if (props.id === "TP01.fragment-field") return <TP01FragmentField {...props} />;
  if (props.id === "TP02.radical-inset") return <TP02RadicalInset {...props} />;
  if (props.id === "TP03.editorial-column") return <TP03EditorialColumn {...props} />;
  if (props.id === "TP04.essay-chorus") return <TP04EssayChorus {...props} />;
  if (props.id === "TP05.annotation-grid") return <TP05AnnotationGrid {...props} />;
  if (props.id === "TP06.spread-cover") return <TP06SpreadCover {...props} />;
  if (props.id === "TP08.spread-quote") return <TP08SpreadQuote {...props} />;
  if (props.id === "TP09.spread-body") return <TP09SpreadBody {...props} />;
  if (props.id === "TP10.geology-ledger") return <TP10GeologyLedger {...props} />;
  if (props.id === "TP11.free-horizon") return <TP11FreeHorizon {...props} />;
  if (props.id === "TP12.perforated-field") return <TP12PerforatedField {...props} />;
  if (props.id === "TP14.waiting-plate") return <TP14WaitingPlate {...props} />;
  return <TP16SpecimenWall {...props} />;
}

export function ArchiveTextPageSurface({
  surface,
  layoutId,
}: {
  surface: Surface;
  layoutId?: TextPageLayoutId;
}) {
  return <TextPageLayout id={layoutId ?? selectTextPageLayout(surface)} surface={surface} />;
}

export default function TextPageLab() {
  const imageRichSample = sampleSurface(
    (surface) => {
      const images = surface.images ?? [];
      return (
        images.length > 0 &&
        images.some((image) => image.state !== "IMG00" && image.state !== "IMG04") &&
        surfaceTextLength(surface) > 420
      );
    },
  );
  const longTextSample = sampleSurface((surface) => surfaceTextLength(surface) > 1800, "SURF-NXS2026R010");

  const verticalImagePages: Array<[TextPageLayoutId, Surface]> = [
    ["TP01.fragment-field", mustSurface("SURF-ER1830R016")],
    ["TP02.radical-inset", mustSurface("SURF-GAPIT2026R002")],
    ["TP03.editorial-column", mustSurface("SURF-GAPIT2026R025")],
    ["TP04.essay-chorus", mustSurface("SURF-LPC2026R034")],
    ["TP05.annotation-grid", imageRichSample],
  ];

  const verticalTextPages: Array<[TextPageLayoutId, Surface]> = [
    ["TP06.spread-cover", mustSurface("SURF-MX1970R066")],
    ["TP08.spread-quote", mustSurface("SURF-NXS2026R010")],
    ["TP09.spread-body", mustSurface("SURF-NXS2026R010")],
  ];

  const horizontalPages: Array<[TextPageLayoutId, Surface]> = [
    ["TP10.geology-ledger", longTextSample],
    ["TP11.free-horizon", mustSurface("SURF-LPC2026R096")],
  ];

  const experimentalVerticalPages: Array<[TextPageLayoutId, Surface]> = [
    ["TP12.perforated-field", mustSurface("SURF-CHW2026R001")],
    ["TP14.waiting-plate", mustSurface("SURF-ER1830R016")],
    ["TP16.source-dossier", mustSurface("SURF-GAPIT2026R025")],
  ];

  return (
    <main className="text-page-lab">
      <header className="text-page-lab__header">
        <p>MGD Archive / text page studies</p>
        <h1>Text Page</h1>
        <span>
          group 01 vertical image / group 02 vertical text as spread logic /
          group 03 horizontal 2:3 / group 04 experimental vertical
        </span>
      </header>

      <section
        className="text-page-lab__group"
        data-text-group="image"
        aria-label="Vertical image text pages"
      >
        <div className="text-page-lab__group-head">
          <p>Group 01</p>
          <h2>Vertical / Image + Text</h2>
          <span>
            image treated as fragment, inset, evidence slice, or marginal crop
            rather than a single hero field
          </span>
        </div>
        <div className="text-page-lab__grid text-page-lab__grid--vertical-five">
          {verticalImagePages.map(([id, surface]) => (
            <TextPageLayout key={id} id={id} surface={surface} />
          ))}
        </div>
      </section>

      <section
        className="text-page-lab__group"
        data-text-group="text"
        aria-label="Vertical pure text pages"
      >
        <div className="text-page-lab__group-head">
          <p>Group 02</p>
          <h2>Vertical / Spread-led Text</h2>
          <span>
            text is curated as paired reading leaves: title leaf, then body
            leaf, instead of collapsing every level into a single page
          </span>
        </div>
        <div className="text-page-lab__grid text-page-lab__grid--vertical-three">
          {verticalTextPages.map(([id, surface]) => (
            <TextPageLayout key={`${id}-${surface.surfaceId}`} id={id} surface={surface} />
          ))}
        </div>
      </section>

      <section
        className="text-page-lab__group"
        data-text-group="horizontal"
        aria-label="Horizontal text pages"
      >
        <div className="text-page-lab__group-head">
          <p>Group 03</p>
          <h2>Horizontal / 2:3</h2>
          <span>
            freer landscape pages with denser modular information and more
            room for typographic pacing
          </span>
        </div>
        <div className="text-page-lab__grid text-page-lab__grid--horizontal">
          {horizontalPages.map(([id, surface]) => (
            <TextPageLayout key={id} id={id} surface={surface} />
          ))}
        </div>
      </section>

      <section
        className="text-page-lab__group"
        data-text-group="experimental"
        aria-label="Experimental vertical text pages"
      >
        <div className="text-page-lab__group-head">
          <p>Group 04</p>
          <h2>Vertical / Experimental Free</h2>
          <span>
            freer vertical pages: perforated register, image/text displacement,
            and source dossier
          </span>
        </div>
        <div className="text-page-lab__grid text-page-lab__grid--vertical-five">
          {experimentalVerticalPages.map(([id, surface]) => (
            <TextPageLayout key={id} id={id} surface={surface} />
          ))}
        </div>
      </section>
    </main>
  );
}
