"use client";

import { useEffect, useMemo, useState } from "react";
import type { FolderTypeKey, PublicSurfaceMock, Surface, SurfaceImage, SurfaceTable } from "@/types/archive";
import { FOLDER_INK } from "@/lib/archive-data";
import type { SubSheetLayoutId } from "@/lib/sub-sheet-layout";

const GROUP_01_STUDIES: Array<[SubSheetLayoutId, string]> = [
  ["SS01.schedule-index", "SURF-LPC2026R034"],
  ["SS02.redline-cv", "SURF-CHW2026R066"],
  ["SS03.day-column", "SURF-GA1970R001"],
  ["SS04.resume-dossier", "SURF-ER1830R016"],
];

const GROUP_02_STUDIES: Array<[SubSheetLayoutId, string]> = [
  ["SS05.layered-menu", "SURF-GAX1970R021"],
  ["SS06.punched-letter", "SURF-CHW2026R001"],
  ["SS07.invoice-ledger", "SURF-ER1830R001-GROUP"],
  ["SS08.cv-sections", "SURF-SI1970R001"],
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
  return surface.folders.map((folder) => [folder.type, folder.title] as [string, string]);
}

function sourceSections(surface: Surface, maxRows = 8): Array<[string, string]> {
  const source = sourceList(surface, maxRows);
  const folders = classificationList(surface).slice(0, 4);
  return [...source, ...folders].slice(0, maxRows);
}

function SS01ScheduleIndex({ surface }: { surface: Surface }) {
  const schedule: Array<[string, string]> = [
    ["source", surface.sourceName],
    ["date", surface.dateText],
    ["object", surface.objectType],
    ["medium", surface.medium],
    ["rights", surface.rights.label],
  ];
  return (
    <article className="sub-sheet sub-sheet--schedule-index" data-sub-sheet="SS01.schedule-index">
      <header>
        <div>{folderBadges(surface)}</div>
        <span>{compactId(surface)} / source scroll</span>
      </header>
      <section className="sub-sheet__scroll-hero">
        <p aria-hidden>sub sheet</p>
        <h2>{clip(surface.title, 46)}</h2>
        <strong>{surface.image.state}</strong>
      </section>
      <div className="sub-sheet__scroll-body">
        <MiniRows items={schedule} />
        <p>{pick(surface.descriptionSummary || surface.sourceDescription, 320, 3)}</p>
      </div>
      <Evidence surface={surface} />
      <section className="sub-sheet__scroll-register">
        {classificationList(surface).slice(0, 4).map(([label, value], index) => (
          <div key={`${label}-${value}`}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{label}</strong>
            <p>{clip(value, 40)}</p>
          </div>
        ))}
      </section>
      <footer>
        <span>{compactId(surface)}</span>
        <span>{yearNumber(surface)}</span>
      </footer>
    </article>
  );
}

function SS02RedlineCv({ surface }: { surface: Surface }) {
  const sourceRows = sourceList(surface, 5);
  return (
    <article className="sub-sheet sub-sheet--redline-cv" data-sub-sheet="SS02.redline-cv">
      <header>
        <div>{folderBadges(surface)}</div>
        <span>{compactId(surface)} / evidence seal</span>
        <strong>{yearNumber(surface)}</strong>
      </header>
      <div className="sub-sheet__seal-stage">
        <section className="sub-sheet__seal-title">
          <span>archive sub sheet</span>
          <h2>{clip(surface.title, 28)}</h2>
        </section>
        <Evidence surface={surface} />
        <div className="sub-sheet__ink-seal">
          <span>{surface.image.state}</span>
        </div>
        <p className="sub-sheet__seal-note">
          {pick(surface.descriptionSummary || surface.sourceDescription, 260, 2)}
        </p>
        <section className="sub-sheet__seal-index">
          {sourceRows.map(([label, value], index) => (
            <div key={`${label}-${index}`}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{label}</strong>
              <p>{clip(value, 42)}</p>
            </div>
          ))}
        </section>
        <section className="sub-sheet__seal-classification">
          {classificationList(surface).slice(0, 4).map(([label, value]) => (
            <div key={`${label}-${value}`}>
              <span>{label}</span>
              <strong>{clip(value, 36)}</strong>
            </div>
          ))}
        </section>
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

function SS05LayeredMenu({ surface }: { surface: Surface }) {
  const menuRows = sourceSections(surface, 9);
  return (
    <article className="sub-sheet sub-sheet--layered-menu" data-sub-sheet="SS05.layered-menu">
      <div className="sub-sheet__menu-shadow sub-sheet__menu-shadow--left" aria-hidden>
        {menuRows.slice(0, 5).map(([label], index) => (
          <span key={`${label}-${index}`}>{clip(label, 18)}</span>
        ))}
      </div>
      <div className="sub-sheet__menu-shadow sub-sheet__menu-shadow--right" aria-hidden>
        {menuRows.slice(4, 9).map(([, value], index) => (
          <span key={`${value}-${index}`}>{String(index + 1).padStart(3, "0")}</span>
        ))}
      </div>
      <header>
        <div>{folderBadges(surface)}</div>
        <span>{compactId(surface)}</span>
        <strong>{yearNumber(surface)}</strong>
      </header>
      <section className="sub-sheet__menu-card">
        <p>source menu</p>
        <h2>{clip(surface.title, 34)}</h2>
        <div className="sub-sheet__menu-list">
          {menuRows.map(([label, value], index) => (
            <div key={`${label}-${index}`}>
              <span>{clip(label, 16)}</span>
              <strong>{clip(value, 34)}</strong>
              <em>{String(index + 1).padStart(2, "0")}</em>
            </div>
          ))}
        </div>
        <Evidence surface={surface} />
        <footer>
          <span>{surface.sourceName}</span>
          <span>{surface.image.state}</span>
        </footer>
      </section>
    </article>
  );
}

function SS06PunchedLetter({ surface }: { surface: Surface }) {
  const quoteRows: Array<[string, string]> = [
    ["for", surface.sourceName],
    ["issued", surface.dateText],
    ["record", compactId(surface)],
    ["policy", surface.rights.displayPolicy],
  ];
  return (
    <article className="sub-sheet sub-sheet--punched-letter" data-sub-sheet="SS06.punched-letter">
      <div className="sub-sheet__punches" aria-hidden>
        {Array.from({ length: 6 }).map((_, index) => (
          <span key={index} />
        ))}
      </div>
      <header>
        <div>{folderBadges(surface)}</div>
        <span>archive quotation</span>
        <strong>page 2/4</strong>
      </header>
      <section className="sub-sheet__letter-address">
        <p>To: MGD Archive / Sub Sheet Register</p>
        <p>{surface.sourceName}</p>
      </section>
      <section className="sub-sheet__letter-title">
        <h2>{clip(surface.title, 38)}</h2>
        <strong>{yearNumber(surface)}</strong>
      </section>
      <MiniRows items={quoteRows} />
      <p className="sub-sheet__letter-copy">
        {pick(surface.descriptionSummary || surface.sourceDescription, 430, 4)}
      </p>
      <div className="sub-sheet__letter-table">
        {sourceSections(surface, 5).map(([label, value], index) => (
          <div key={`${label}-${index}`}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{clip(label, 18)}</strong>
            <p>{clip(value, 58)}</p>
          </div>
        ))}
      </div>
      <footer>
        <span>{compactId(surface)}</span>
        <span>{surface.image.state}</span>
      </footer>
    </article>
  );
}

function SS07InvoiceLedger({ surface }: { surface: Surface }) {
  const items = sourceSections(surface, 7);
  return (
    <article className="sub-sheet sub-sheet--invoice-ledger" data-sub-sheet="SS07.invoice-ledger">
      <header>
        <div className="sub-sheet__ledger-mark">{surface.image.state}</div>
        <div>
          <span>invoice number</span>
          <strong>{compactId(surface)}</strong>
        </div>
        <div>
          <span>invoice date</span>
          <strong>{surface.dateText}</strong>
        </div>
      </header>
      <section className="sub-sheet__ledger-address">
        <p>A:</p>
        <strong>{surface.sourceName}</strong>
        <span>{surface.rights.label}</span>
      </section>
      <section className="sub-sheet__ledger-table">
        <div>
          <span>qty</span>
          <span>description</span>
          <span>source</span>
        </div>
        {items.map(([label, value], index) => (
          <div key={`${label}-${index}`}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{clip(value, 48)}</strong>
            <span>{clip(label, 16)}</span>
          </div>
        ))}
      </section>
      <section className="sub-sheet__ledger-pay">
        <p>{pick(surface.descriptionSummary || surface.sourceDescription, 260, 3)}</p>
        <MiniRows
          items={[
            ["type", surface.objectType],
            ["medium", surface.medium],
            ["image", surface.image.state],
          ]}
        />
      </section>
      <footer>
        <span>{surface.creator || "unknown creator"}</span>
        <span>{compactId(surface)}</span>
      </footer>
    </article>
  );
}

function SS08CvSections({ surface }: { surface: Surface }) {
  const sections = [
    ["source", sourceList(surface, 4)],
    ["folders", classificationList(surface).slice(0, 4)],
    [
      "record",
      [
        ["date", surface.dateText],
        ["type", surface.objectType],
        ["medium", surface.medium],
      ] as Array<[string, string]>,
    ],
  ] as const;
  return (
    <article className="sub-sheet sub-sheet--cv-sections" data-sub-sheet="SS08.cv-sections">
      <header>
        <h2>{clip(surface.title, 28)}</h2>
        <span>{compactId(surface)}</span>
      </header>
      <aside>
        <Evidence surface={surface} />
        <strong>CV</strong>
        <p>{surface.sourceName}</p>
      </aside>
      <section className="sub-sheet__cv-summary">
        <h3>{surface.objectType}</h3>
        <p>{pick(surface.descriptionSummary || surface.sourceDescription, 320, 3)}</p>
      </section>
      <section className="sub-sheet__cv-columns">
        {sections.map(([title, items]) => (
          <div key={title}>
            <h3>{title}</h3>
            <MiniRows items={items} />
          </div>
        ))}
      </section>
      <footer>
        <span>{yearNumber(surface)}</span>
        <span>{surface.image.state}</span>
        <span>sub sheet</span>
      </footer>
    </article>
  );
}

export function ArchiveSubSheetSurface({ id, surface }: { id: SubSheetLayoutId; surface: Surface }) {
  if (id === "SS01.schedule-index") return <SS01ScheduleIndex surface={surface} />;
  if (id === "SS02.redline-cv") return <SS02RedlineCv surface={surface} />;
  if (id === "SS03.day-column") return <SS03DayColumn surface={surface} />;
  if (id === "SS04.resume-dossier") return <SS04ResumeDossier surface={surface} />;
  if (id === "SS05.layered-menu") return <SS05LayeredMenu surface={surface} />;
  if (id === "SS06.punched-letter") return <SS06PunchedLetter surface={surface} />;
  if (id === "SS07.invoice-ledger") return <SS07InvoiceLedger surface={surface} />;
  return <SS08CvSections surface={surface} />;
}

export default function SubSheetLab() {
  const [payload, setPayload] = useState<PublicSurfaceMock | null>(null);

  useEffect(() => {
    fetch("/data/public_surface_mock_v0.json")
      .then((response) => response.json())
      .then((data: PublicSurfaceMock) => setPayload(data));
  }, []);

  const groups = useMemo(() => {
    if (!payload) return [];
    return [
      {
        id: "group-01",
        title: "Sub Sheet Group 01",
        description:
          "frozen first group: source scroll, ink seal dossier, day column, and resume dossier",
        studies: GROUP_01_STUDIES,
      },
      {
        id: "group-02",
        title: "Sub Sheet Group 02",
        description:
          "second group: layered menu, punched letter, invoice ledger, and CV section sheet",
        studies: GROUP_02_STUDIES,
      },
    ].map((group) => ({
      ...group,
      surfaces: group.studies.map(([id, surfaceId]) => {
        const surface = payload.surfaces.find((entry) => entry.surfaceId === surfaceId);
        if (!surface) throw new Error(`Missing sub-sheet study surface: ${surfaceId}`);
        return [id, surface] as const;
      }),
    }));
  }, [payload]);

  if (!payload) {
    return <main className="sub-sheet-lab sub-sheet-lab--loading">Loading sub sheet studies</main>;
  }

  return (
    <main className="sub-sheet-lab">
      <header className="sub-sheet-lab__header">
        <p>MGD Archive / sub sheet studies</p>
        <h1>Sub Sheet Groups</h1>
        <span>group 01 frozen; group 02 explores lower-level document systems</span>
      </header>
      {groups.map((group) => (
        <section className="sub-sheet-lab__set" key={group.id}>
          <header className="sub-sheet-lab__set-header">
            <span>{group.id}</span>
            <h2>{group.title}</h2>
            <p>{group.description}</p>
          </header>
          <div className="sub-sheet-lab__group" data-sub-sheet-group={group.id}>
            {group.surfaces.map(([id, surface]) => (
              <ArchiveSubSheetSurface key={id} id={id} surface={surface} />
            ))}
          </div>
        </section>
      ))}
    </main>
  );
}
