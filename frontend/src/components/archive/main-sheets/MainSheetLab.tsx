"use client";

import { useEffect, useMemo, useState } from "react";
import type { FolderTypeKey, PublicSurfaceMock, Surface, SurfaceTable } from "@/types/archive";
import { FOLDER_INK } from "@/lib/archive-data";
import type { MainSheetLayoutId } from "@/lib/main-sheet-layout";

const STUDIES: Array<[MainSheetLayoutId, string]> = [
  ["MS01.protocol-ledger", "SURF-MC1930R021"],
  ["MS02.evidence-dossier", "SURF-GAPIT2026R025"],
  ["MS03.split-bulletin", "SURF-CHW2026R066"],
  ["MS04.grid-register", "SURF-ER1830R016"],
];

function clean(value: string | null | undefined): string {
  return value?.replace(/\\n/g, " ").replace(/\s+/g, " ").trim() || "unrecorded";
}

function clipWords(value: string | null | undefined, maxWords: number): string {
  const words = clean(value).split(" ").filter(Boolean);
  return words.slice(0, maxWords).join(" ");
}

function clipValue(value: string | null | undefined, max = 92): string {
  const cleaned = clean(value);
  if (cleaned.length <= max) return cleaned;
  return `${cleaned.slice(0, max - 1).trim()}...`;
}

function sentenceSplit(value: string | null | undefined): string[] {
  return clean(value)
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function pickSentences(
  value: string | null | undefined,
  maxChars: number,
  maxSentences = 3,
): string {
  const sentences = sentenceSplit(value);
  const out: string[] = [];
  let length = 0;
  for (const sentence of sentences) {
    const next = length + sentence.length + (out.length ? 1 : 0);
    if (out.length && next > maxChars) break;
    out.push(sentence);
    length = next;
    if (out.length >= maxSentences) break;
  }
  return out.join(" ") || clipWords(value, Math.max(12, Math.floor(maxChars / 7)));
}

function table(surface: Surface, kind: string): SurfaceTable | undefined {
  return surface.tables.find((entry) => entry.kind === kind);
}

function tableRows(surface: Surface, kind: string, maxRows: number): Array<[string, string]> {
  return table(surface, kind)?.rows.slice(0, maxRows) ?? [];
}

function summaryRows(
  surface: Surface,
  kind: string,
  maxRows: number,
  maxChars = 92,
): Array<[string, string]> {
  return tableRows(surface, kind, maxRows).map(([label, value]) => [
    clipValue(label, 34),
    clipValue(value, maxChars),
  ]);
}

function breakKind(value: string): "anywhere" | "normal" {
  return /https?:\/\/|www\.|[A-Z]{2,}\d{2,}|^[A-Z0-9_.:/-]{8,}$/i.test(value)
    ? "anywhere"
    : "normal";
}

function compactId(surface: Surface): string {
  return surface.sourceRecordId.replace(/^REC-/, "").replace(/^SURF-/, "");
}

function folderBadges(surface: Surface) {
  return surface.folders.map((folder) => (
    <span
      key={folder.folderId}
      className="main-sheet-badge"
      style={{ background: FOLDER_INK[folder.type as FolderTypeKey] ?? "#19150f" }}
      title={`${folder.type}: ${folder.title}`}
    />
  ));
}

function imageUrl(surface: Surface): string | null {
  if (surface.image.url && ["IMG01", "IMG02", "IMG03"].includes(surface.image.state)) {
    return surface.image.url;
  }
  return null;
}

function EvidencePlate({
  surface,
  mode = "contain",
}: {
  surface: Surface;
  mode?: "contain" | "cover";
}) {
  const url = imageUrl(surface);
  if (surface.image.state === "IMG04") {
    return null;
  }
  return (
    <figure className="main-sheet-plate">
      <div className="main-sheet-plate__frame">
        {url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={url}
            alt={surface.image.credit ?? surface.title}
            referrerPolicy="no-referrer"
            className={mode === "cover" ? "is-cover" : ""}
          />
        ) : (
          <div className="main-sheet-plate__empty">
            <span>{surface.image.state}</span>
            <p>image evidence reserved at source</p>
          </div>
        )}
      </div>
      <figcaption>
        <span>{surface.image.state}</span>
        <span>{surface.sourceName}</span>
      </figcaption>
    </figure>
  );
}

function MiniTable({
  rows,
  className = "",
}: {
  rows: Array<[string, string]>;
  className?: string;
}) {
  return (
    <table className={`main-sheet-mini-table ${className}`}>
      <tbody>
        {rows.map(([label, value], index) => (
          <tr key={`${label}-${index}`}>
            <th>{label}</th>
            <td data-break={breakKind(value)}>{value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function DotRows({
  rows,
}: {
  rows: Array<[string, string]>;
}) {
  return (
    <div className="main-sheet-dot-rows">
      {rows.map(([label, value], index) => (
        <div key={`${label}-${index}`}>
          <span className="num">[{String(index + 1).padStart(2, "0")}]</span>
          <span className="dots" />
          <strong>{label}</strong>
          <em data-break={breakKind(value)}>{value}</em>
        </div>
      ))}
    </div>
  );
}

function fieldRows(surface: Surface): Array<[string, string]> {
  return [
    ["date", clipValue(surface.dateText, 54)],
    ["type", clipValue(surface.objectType, 48)],
    ["medium", clipValue(surface.medium, 52)],
    ["creator", clipValue(surface.creator || "unrecorded", 78)],
    ["place", clipValue(surface.placeText || "unrecorded", 58)],
    ["source", clipValue(surface.sourceName, 78)],
    ["accessed", clipValue(surface.accessDate, 44)],
  ];
}

function classificationRows(surface: Surface): Array<[string, string]> {
  return surface.folders.map((folder) => [folder.type, folder.title]);
}

function MS01ProtocolLedger({ surface }: { surface: Surface }) {
  const sourceRows = summaryRows(surface, "SOURCE", 2, 64);
  const classRows = classificationRows(surface).slice(0, 3).map(([label, value]) => [
    clipValue(label, 24),
    clipValue(value, 54),
  ] as [string, string]);
  return (
    <article className="main-sheet main-sheet--protocol-ledger" data-main-sheet="MS01.protocol-ledger" data-image-state={surface.image.state}>
      <CornerMarks />
      <header className="main-sheet__terminal-head">
        <div>{folderBadges(surface)}</div>
        <span>{compactId(surface)}</span>
        <span>{surface.image.state}</span>
      </header>
      <div className="main-sheet__heavy-rule" />
      <section className="main-sheet__protocol-title">
        <p>MAIN / SHEET / RECORD</p>
        <h2>{surface.title}</h2>
      </section>
      <div className="main-sheet__protocol-grid">
        <div>
          <h3>01 / OBJECT CONTROL</h3>
          <DotRows rows={fieldRows(surface).slice(0, 3)} />
        </div>
        <div>
          <EvidencePlate surface={surface} />
        </div>
      </div>
      <section className="main-sheet__protocol-text">
        <h3>02 / ABSTRACT</h3>
        <p>{pickSentences(surface.descriptionSummary || surface.sourceDescription, 230, 2)}</p>
      </section>
      <section className="main-sheet__two-up">
        <div>
          <h3>03 / SOURCE</h3>
          <MiniTable rows={sourceRows} />
        </div>
        <div>
          <h3>04 / FOLDERS</h3>
          <DotRows rows={classRows} />
        </div>
      </section>
      <FooterBar id="MS01.PROTOCOL-LEDGER" surface={surface} />
    </article>
  );
}

function MS02EvidenceDossier({ surface }: { surface: Surface }) {
  const rows: Array<[string, string]> = [
    ...fieldRows(surface).slice(0, 4),
    ["rights", surface.rights.state],
    ["policy", surface.rights.displayPolicy],
  ];
  return (
    <article className="main-sheet main-sheet--evidence-dossier" data-main-sheet="MS02.evidence-dossier" data-image-state={surface.image.state}>
      <CornerMarks />
      <header className="main-sheet__dossier-head">
        <div>
          <span>MS02</span>
          <h2>{surface.title}</h2>
        </div>
        <div className="main-sheet__dossier-number">
          {String(surface.completenessScore).padStart(2, "0")}
        </div>
      </header>
      <div className="main-sheet__dossier-rule">
        <span>{surface.dateText}</span>
        <span>{surface.sourceName}</span>
        <span>{folderBadges(surface)}</span>
      </div>
      <div className="main-sheet__dossier-grid">
        <div className="main-sheet__dossier-copy">
          <p className="lead">{pickSentences(surface.descriptionSummary, 280, 2)}</p>
          <p>{pickSentences(surface.sourceDescription, 360, 3)}</p>
          <div className="main-sheet__black-note">
            <strong>source-return context</strong>
            <span>{pickSentences(surface.citationBasis || surface.classificationRationale, 200, 2)}</span>
          </div>
        </div>
        <div>
          <EvidencePlate surface={surface} />
          <MiniTable rows={rows} />
        </div>
      </div>
      <FooterBar id="MS02.EVIDENCE-DOSSIER" surface={surface} />
    </article>
  );
}

function MS03SplitBulletin({ surface }: { surface: Surface }) {
  const sourceRows = summaryRows(surface, "NORMALIZED", 4, 72);
  return (
    <article className="main-sheet main-sheet--split-bulletin" data-main-sheet="MS03.split-bulletin" data-image-state={surface.image.state}>
      <div className="main-sheet__split-left">
        <div>{folderBadges(surface)}</div>
        <p>ARCHIVE MAIN SHEET</p>
        <h2>{surface.title}</h2>
        <span>{surface.dateText}</span>
        <strong>{surface.objectType}</strong>
        <small>{surface.medium}</small>
      </div>
      <div className="main-sheet__split-right">
        <header>
          <span>{compactId(surface)}</span>
          <span>{surface.image.state}</span>
          <span>{surface.sourceName}</span>
        </header>
        <div className="main-sheet__split-content">
          <div>
            <p className="main-sheet__large-copy">
              {pickSentences(surface.descriptionSummary || surface.sourceDescription, 300, 3)}
            </p>
            <MiniTable rows={sourceRows} />
          </div>
          <EvidencePlate surface={surface} mode="cover" />
        </div>
        <div className="main-sheet__split-register">
          <DotRows rows={classificationRows(surface)} />
        </div>
      </div>
    </article>
  );
}

function MS04GridRegister({ surface }: { surface: Surface }) {
  const sourceRows = summaryRows(surface, "SOURCE", 3, 68);
  const rightsRows = summaryRows(surface, "RIGHTS", 3, 68);
  const classRows = summaryRows(surface, "CLASSIFICATION", 4, 64);
  return (
    <article className="main-sheet main-sheet--grid-register" data-main-sheet="MS04.grid-register" data-image-state={surface.image.state}>
      <CornerMarks />
      <div className="main-sheet__grid-lines" aria-hidden />
      <header className="main-sheet__grid-head">
        <div>
          <span>{folderBadges(surface)}</span>
          <p>{compactId(surface)} / MAIN SHEET</p>
        </div>
        <h2>{surface.title}</h2>
      </header>
      <div className="main-sheet__grid-body">
        <section className="cell cell--lead">
          <h3>record note</h3>
          <p>{pickSentences(surface.descriptionSummary || surface.sourceDescription, 260, 3)}</p>
        </section>
        <section className="cell cell--plate">
          <EvidencePlate surface={surface} />
        </section>
        <section className="cell">
          <h3>source</h3>
          <MiniTable rows={sourceRows} />
        </section>
        <section className="cell">
          <h3>rights</h3>
          <MiniTable rows={rightsRows} />
        </section>
        <section className="cell cell--wide">
          <h3>classification register</h3>
          <MiniTable rows={classRows} />
        </section>
      </div>
      <FooterBar id="MS04.GRID-REGISTER" surface={surface} />
    </article>
  );
}

function CornerMarks() {
  return (
    <>
      <span className="main-sheet-corner main-sheet-corner--tl" />
      <span className="main-sheet-corner main-sheet-corner--tr" />
      <span className="main-sheet-corner main-sheet-corner--bl" />
      <span className="main-sheet-corner main-sheet-corner--br" />
    </>
  );
}

function FooterBar({ id, surface }: { id: string; surface: Surface }) {
  return (
    <footer className="main-sheet__footer">
      <span>{id}</span>
      <span>{surface.seqLabel}</span>
      <span>{surface.sourceName}</span>
    </footer>
  );
}

function IMG04TextOnlyMainSheet({ surface }: { surface: Surface }) {
  const sourceRows = summaryRows(surface, "SOURCE", 4, 80);
  const classRows = classificationRows(surface).slice(0, 4);
  return (
    <article className="main-sheet main-sheet--img04-text" data-main-sheet="IMG04.text-only" data-image-state="IMG04">
      <header className="main-sheet__terminal-head">
        <div>{folderBadges(surface)}</div>
        <span>{compactId(surface)}</span>
        <span>IMG04</span>
      </header>
      <section className="main-sheet__img04-title">
        <p>TEXT / ONLY / RECORD</p>
        <h2>{surface.title}</h2>
        <span>no image frame required</span>
      </section>
      <section className="main-sheet__img04-copy">
        <p className="lead">{pickSentences(surface.descriptionSummary || surface.sourceDescription, 360, 3)}</p>
        <p>{pickSentences(surface.sourceDescription || surface.historicalContextNote || surface.classificationRationale, 520, 4)}</p>
      </section>
      <section className="main-sheet__img04-ledgers">
        <div>
          <h3>source summary</h3>
          <MiniTable rows={sourceRows} />
        </div>
        <div>
          <h3>folder metadata</h3>
          <DotRows rows={classRows} />
        </div>
      </section>
      <FooterBar id="IMG04.TEXT-ONLY" surface={surface} />
    </article>
  );
}

export function ArchiveMainSheetSurface({ id, surface }: { id: MainSheetLayoutId; surface: Surface }) {
  if (surface.image.state === "IMG04") return <IMG04TextOnlyMainSheet surface={surface} />;
  if (id === "MS01.protocol-ledger") return <MS01ProtocolLedger surface={surface} />;
  if (id === "MS02.evidence-dossier") return <MS02EvidenceDossier surface={surface} />;
  if (id === "MS03.split-bulletin") return <MS03SplitBulletin surface={surface} />;
  return <MS04GridRegister surface={surface} />;
}

export default function MainSheetLab() {
  const [payload, setPayload] = useState<PublicSurfaceMock | null>(null);

  useEffect(() => {
    fetch("/data/public_surface_mock_v0.json")
      .then((response) => response.json())
      .then((data: PublicSurfaceMock) => setPayload(data));
  }, []);

  const surfaces = useMemo(() => {
    if (!payload) return [];
    return STUDIES.map(([id, surfaceId]) => {
      const surface = payload.surfaces.find((entry) => entry.surfaceId === surfaceId);
      if (!surface) throw new Error(`Missing main-sheet study surface: ${surfaceId}`);
      return [id, surface] as const;
    });
  }, [payload]);

  if (!payload) {
    return <main className="main-sheet-lab main-sheet-lab--loading">Loading main sheet studies</main>;
  }

  return (
    <main className="main-sheet-lab">
      <header className="main-sheet-lab__header">
        <p>MGD Archive / main sheet studies</p>
        <h1>Main Sheet Group 01</h1>
        <span>
          four different directions: protocol ledger, evidence dossier, split
          bulletin, and grid register
        </span>
      </header>
      <section className="main-sheet-lab__group" data-main-sheet-group="group-01">
        {surfaces.map(([id, surface]) => (
          <ArchiveMainSheetSurface key={id} id={id} surface={surface} />
        ))}
      </section>
    </main>
  );
}
