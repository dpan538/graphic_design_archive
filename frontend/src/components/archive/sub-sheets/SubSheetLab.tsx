"use client";

import { useEffect, useMemo, useState } from "react";
import type { FolderTypeKey, PublicSurfaceMock, Surface, SurfaceImage, SurfaceTable } from "@/types/archive";
import { FOLDER_INK } from "@/lib/archive-data";
import type { SubSheetLayoutId } from "@/lib/sub-sheet-layout";

const STUDIES: Array<[SubSheetLayoutId, string]> = [
  ["SS01.schedule-index", "SURF-LPC2026R034"],
  ["SS02.redline-cv", "SURF-CHW2026R066"],
  ["SS03.day-column", "SURF-GA1970R001"],
  ["SS04.resume-dossier", "SURF-ER1830R016"],
];

function clean(value: string | null | undefined): string {
  return value?.replace(/\\n/g, " ").replace(/\s+/g, " ").trim() || "unrecorded";
}

function clip(value: string | null | undefined, maxChars: number): string {
  const text = clean(value);
  return text.length > maxChars ? `${text.slice(0, maxChars - 1).trim()}…` : text;
}

function sentences(value: string | null | undefined): string[] {
  return clean(value)
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function pick(value: string | null | undefined, maxChars: number, maxSentences = 3): string {
  const out: string[] = [];
  let length = 0;
  for (const sentence of sentences(value)) {
    const next = length + sentence.length + (out.length ? 1 : 0);
    if (out.length && next > maxChars) break;
    out.push(sentence);
    length = next;
    if (out.length >= maxSentences) break;
  }
  return out.join(" ") || clip(value, maxChars);
}

function table(surface: Surface, kind: string): SurfaceTable | undefined {
  return surface.tables.find((entry) => entry.kind === kind);
}

function rows(surface: Surface, kind: string, maxRows: number): Array<[string, string]> {
  return table(surface, kind)?.rows.slice(0, maxRows) ?? [];
}

function compactId(surface: Surface): string {
  return surface.sourceRecordId.replace(/^REC-/, "").replace(/^SURF-/, "");
}

function yearNumber(surface: Surface): string {
  const match = clean(surface.dateText).match(/\d{4}/);
  return match?.[0] ?? String(surface.dateStart ?? "----");
}

function imageUrl(image: SurfaceImage | undefined): string | null {
  if (image?.url && ["IMG01", "IMG02", "IMG03"].includes(image.state)) return image.url;
  return null;
}

function folderBadges(surface: Surface) {
  return surface.folders.map((folder) => (
    <span
      key={folder.folderId}
      className="sub-sheet-badge"
      style={{ background: FOLDER_INK[folder.type as FolderTypeKey] ?? "#19150f" }}
      title={`${folder.type}: ${folder.title}`}
    />
  ));
}

function MiniRows({
  items,
  className = "",
}: {
  items: Array<[string, string]>;
  className?: string;
}) {
  return (
    <div className={`sub-sheet-mini-rows ${className}`}>
      {items.map(([label, value], index) => (
        <div key={`${label}-${index}`}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function Evidence({
  surface,
  className = "",
}: {
  surface: Surface;
  className?: string;
}) {
  const url = imageUrl(surface.image);
  return (
    <figure className={`sub-sheet-evidence ${className}`}>
      <div>
        {url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={url} alt={surface.image.credit ?? surface.title} referrerPolicy="no-referrer" />
        ) : (
          <span>{surface.image.state}</span>
        )}
      </div>
      <figcaption>
        <span>{surface.image.state}</span>
        <span>{surface.sourceName}</span>
      </figcaption>
    </figure>
  );
}

function sourceList(surface: Surface, count: number): Array<[string, string]> {
  const source = rows(surface, "SOURCE", count);
  if (source.length) return source;
  return [
    ["source", surface.sourceName],
    ["date", surface.dateText],
    ["type", surface.objectType],
  ];
}

function classificationList(surface: Surface): Array<[string, string]> {
  return surface.folders.map((folder) => [folder.type, folder.title]);
}

function SS01ScheduleIndex({ surface }: { surface: Surface }) {
  const schedule = [
    ["source", surface.sourceName],
    ["date", surface.dateText],
    ["object", surface.objectType],
    ["medium", surface.medium],
    ["rights", surface.rights.label],
    ["basis", surface.citationBasis || surface.classificationRationale || surface.sourceName],
  ];
  return (
    <article className="sub-sheet sub-sheet--schedule-index" data-sub-sheet="SS01.schedule-index">
      <header>
        <h2>{clip(surface.title, 32)}</h2>
        <div>{folderBadges(surface)}</div>
      </header>
      <section className="sub-sheet__schedule-stack">
        {schedule.map(([label, value], index) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{index + 1}.{index + 2}</strong>
            <p>{clip(value, 58)}</p>
          </div>
        ))}
      </section>
      <p className="sub-sheet__schedule-copy">
        {pick(surface.descriptionSummary || surface.sourceDescription, 340, 3)}
      </p>
      <footer>
        <span>{compactId(surface)}</span>
        <span>{surface.image.state}</span>
        <span>SUB SHEET / 0.9</span>
      </footer>
    </article>
  );
}

function SS02RedlineCv({ surface }: { surface: Surface }) {
  return (
    <article className="sub-sheet sub-sheet--redline-cv" data-sub-sheet="SS02.redline-cv">
      <div className="sub-sheet__red-grid" aria-hidden />
      <header>
        <span>{compactId(surface)}</span>
        <h2>{clip(surface.title, 30)}</h2>
        <strong>{yearNumber(surface)}</strong>
      </header>
      <div className="sub-sheet__red-body">
        <Evidence surface={surface} />
        <section>
          <h3>archive sub sheet</h3>
          <p>{pick(surface.descriptionSummary || surface.sourceDescription, 300, 3)}</p>
        </section>
        <MiniRows items={sourceList(surface, 4)} />
        <MiniRows items={classificationList(surface).slice(0, 4)} className="is-right" />
      </div>
      <footer>
        <span>{surface.sourceName}</span>
        <span>{surface.rights.displayPolicy}</span>
      </footer>
    </article>
  );
}

function SS03DayColumn({ surface }: { surface: Surface }) {
  const year = yearNumber(surface);
  const digits = year.split("");
  return (
    <article className="sub-sheet sub-sheet--day-column" data-sub-sheet="SS03.day-column">
      <header>
        <span>{compactId(surface)}</span>
        <span>{surface.sourceName}</span>
      </header>
      <aside>
        {digits.map((digit, index) => (
          <strong key={`${digit}-${index}`}>{digit}</strong>
        ))}
      </aside>
      <section className="sub-sheet__day-main">
        <h2>{clip(surface.title, 44)}</h2>
        <p>{pick(surface.descriptionSummary || surface.sourceDescription, 260, 3)}</p>
      </section>
      <Evidence surface={surface} />
      <MiniRows items={sourceList(surface, 5)} />
      <footer>
        <span>{surface.dateText}</span>
        <span>{surface.image.state}</span>
        <span>{surface.objectType}</span>
      </footer>
    </article>
  );
}

function SS04ResumeDossier({ surface }: { surface: Surface }) {
  const metadata: Array<[string, string]> = [
    ["date", surface.dateText],
    ["creator", surface.creator || "unrecorded"],
    ["place", surface.placeText || "unrecorded"],
    ["type", surface.objectType],
    ["medium", surface.medium],
  ];
  return (
    <article className="sub-sheet sub-sheet--resume-dossier" data-sub-sheet="SS04.resume-dossier">
      <header>
        <span>sub sheet</span>
        <h2>{clip(surface.title, 32)}</h2>
        <strong>{yearNumber(surface)}</strong>
      </header>
      <div className="sub-sheet__resume-top">
        <MiniRows items={metadata} />
        <Evidence surface={surface} />
      </div>
      <p className="sub-sheet__resume-statement">
        {pick(surface.descriptionSummary || surface.sourceDescription, 360, 3)}
      </p>
      <div className="sub-sheet__resume-bottom">
        <MiniRows items={classificationList(surface).slice(0, 4)} />
        <MiniRows items={rows(surface, "RIGHTS", 3)} />
      </div>
      <footer>
        <span>{compactId(surface)}</span>
        <span>{surface.sourceName}</span>
      </footer>
    </article>
  );
}

function SubSheetLayout({ id, surface }: { id: SubSheetLayoutId; surface: Surface }) {
  if (id === "SS01.schedule-index") return <SS01ScheduleIndex surface={surface} />;
  if (id === "SS02.redline-cv") return <SS02RedlineCv surface={surface} />;
  if (id === "SS03.day-column") return <SS03DayColumn surface={surface} />;
  return <SS04ResumeDossier surface={surface} />;
}

export default function SubSheetLab() {
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
      if (!surface) throw new Error(`Missing sub-sheet study surface: ${surfaceId}`);
      return [id, surface] as const;
    });
  }, [payload]);

  if (!payload) {
    return <main className="sub-sheet-lab sub-sheet-lab--loading">Loading sub sheet studies</main>;
  }

  return (
    <main className="sub-sheet-lab">
      <header className="sub-sheet-lab__header">
        <p>MGD Archive / sub sheet studies</p>
        <h1>Sub Sheet Group 01</h1>
        <span>
          four directions below main sheet weight: schedule index, redline CV,
          day column, and resume dossier
        </span>
      </header>
      <section className="sub-sheet-lab__group" data-sub-sheet-group="group-01">
        {surfaces.map(([id, surface]) => (
          <SubSheetLayout key={id} id={id} surface={surface} />
        ))}
      </section>
    </main>
  );
}
