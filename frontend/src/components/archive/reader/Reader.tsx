"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { FolderTypeKey, ResearchDossier } from "@/types/archive";
import {
  surfaceLeafIndex,
  type JumpTarget,
  type Leaf,
} from "@/lib/paginate";
import type { LeafCtx } from "../layouts";
import ArchiveShell from "../shell/ArchiveShell";
import LeafFrame from "./LeafFrame";

interface ReaderProps {
  leaves: Leaf[];
  jumpTargets: JumpTarget[];
  initialIndex?: number;
  activeFolderId?: string;
  folderInk: string;
  folderType?: FolderTypeKey;
  researchDossiers?: ResearchDossier[];
  contextTitle: string;
  contextSubtitle: string;
  backHref?: string;
  backLabel?: string;
}

export default function Reader({
  leaves,
  jumpTargets,
  initialIndex = 0,
  activeFolderId,
  folderInk,
  researchDossiers = [],
  contextTitle,
  contextSubtitle,
  backHref,
  backLabel,
}: ReaderProps) {
  const [index, setIndex] = useState(
    Math.min(Math.max(initialIndex, 0), leaves.length - 1),
  );

  const next = useCallback(
    () => setIndex((i) => Math.min(i + 1, leaves.length - 1)),
    [leaves.length],
  );
  const prev = useCallback(() => setIndex((i) => Math.max(i - 1, 0)), []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, prev]);

  const sIndex = useMemo(() => surfaceLeafIndex(leaves), [leaves]);
  const ctx: LeafCtx = useMemo(
    () => ({ onJump: (i: number) => setIndex(i), surfaceLeafIndex: sIndex }),
    [sIndex],
  );

  const visible = [leaves[index]].filter(Boolean);
  const activeLeaf = visible[0];
  const activeSurface = activeLeaf?.surface;
  const dossierBySurfaceId = useMemo(() => {
    const map = new Map<string, ResearchDossier>();
    for (const dossier of researchDossiers) {
      map.set(dossier.anchorSurfaceId, dossier);
      for (const page of dossier.pageSequence) {
        if (!map.has(page.surfaceId)) map.set(page.surfaceId, dossier);
      }
    }
    return map;
  }, [researchDossiers]);
  const activeDossier = activeSurface
    ? dossierBySurfaceId.get(activeSurface.surfaceId)
    : undefined;
  const openAssistant = useCallback(() => {
    window.dispatchEvent(
      new CustomEvent("archive:open-assistant", {
        detail: {
          surfaceId: activeSurface?.surfaceId,
          title: activeSurface?.title ?? contextTitle,
          dateText: activeSurface?.dateText ?? contextSubtitle,
          imageState: activeSurface?.image.state,
          rightsLabel: activeSurface?.rights.label,
          sourceName: activeSurface?.sourceName,
          creator: activeSurface?.creator,
          objectType: activeSurface?.objectType,
        },
      }),
    );
  }, [activeSurface, contextSubtitle, contextTitle]);

  const atStart = index <= 0;
  const atEnd = index >= leaves.length - 1;

  const activeTargetIdx = useMemo(() => {
    let active = 0;
    jumpTargets.forEach((t, i) => {
      if (t.leafIndex <= index) active = i;
    });
    return active;
  }, [jumpTargets, index]);
  const mainSheetTargets = useMemo(() => {
    return leaves
      .map((leaf, leafIndex) => ({ leaf, leafIndex }))
      .filter(({ leaf }) => leaf.type === "main" && leaf.surface)
      .map(({ leaf, leafIndex }) => ({
        leafIndex,
        label: leaf.surface?.title ?? "Untitled main sheet",
        sublabel: leaf.surface?.dateText ?? "",
      }));
  }, [leaves]);
  const activeMainSheetIdx = useMemo(() => {
    let active = 0;
    mainSheetTargets.forEach((target, i) => {
      if (target.leafIndex <= index) active = i;
    });
    return active;
  }, [index, mainSheetTargets]);
  const nearbyMainSheetTargets = useMemo(() => {
    const start = Math.max(0, activeMainSheetIdx - 2);
    const end = Math.min(mainSheetTargets.length, activeMainSheetIdx + 3);
    return mainSheetTargets.slice(start, end).map((target, offset) => ({
      target,
      originalIndex: start + offset,
    }));
  }, [activeMainSheetIdx, mainSheetTargets]);
  const showDossierTree =
    activeDossier?.anchorType === "main_sheet" &&
    activeDossier.pageSequence.length > 0;

  const main = (
    <div className="relative flex-1 min-h-0 flex flex-col">
      <div className="leaf-stage">
        <LeafFrame leaf={visible[0]} single activeFolderId={activeFolderId} ctx={ctx} />
      </div>

      <div className="page-turn">
        <button
          type="button"
          className="btn-turn btn-turn--assistant"
          onClick={openAssistant}
          aria-label="Open research assistant"
          title="Research"
        >
          <IconAssistant />
          <span>Research</span>
        </button>
        <div className="page-turn__sep" aria-hidden />
        <button
          type="button"
          className="btn-turn"
          onClick={prev}
          disabled={atStart}
          aria-label="Previous page"
        >
          ‹
        </button>
        <div className="meter">
          <b>{index + 1}</b>
          <span>of {leaves.length}</span>
        </div>
        <button
          type="button"
          className="btn-turn"
          onClick={next}
          disabled={atEnd}
          aria-label="Next page"
        >
          ›
        </button>
      </div>
    </div>
  );

  const contextPanel = (
    <>
      <div className="packet-panel__header">
        {backHref ? (
          <Link href={backHref} className="label-caps underline">
            ← {backLabel ?? "Back"}
          </Link>
        ) : null}
        <div className="font-bold text-lg leading-tight mt-1.5">
          {contextTitle}
        </div>
        <div className="label-caps text-ink-soft mt-1 flex items-center gap-1.5">
          <span
            className="inline-block w-3 h-3 border border-ink"
            style={{ backgroundColor: folderInk }}
            aria-hidden
          />
          {contextSubtitle}
        </div>
      </div>

      <div className="panel-scroll packet-panel__scroll">
        <section className="packet-summary">
          <div className="label-caps text-ink-soft">Background context</div>
          <h3>{activeDossier?.title ?? activeSurface?.title ?? "Register / index"}</h3>
          <dl>
            <div>
              <dt>anchor</dt>
              <dd>{activeDossier ? formatAnchorType(activeDossier.anchorType) : activeLeaf?.type ?? "folder"}</dd>
            </div>
            <div>
              <dt>scope</dt>
              <dd>{activeDossier ? formatScope(activeDossier.sourceScope) : "folder register"}</dd>
            </div>
            <div>
              <dt>basis</dt>
              <dd>{activeDossier?.groupingBasis ?? "chronological folder sequence"}</dd>
            </div>
            <div>
              <dt>pages</dt>
              <dd>{activeDossier?.pageCount ?? leaves.length}</dd>
            </div>
          </dl>
        </section>

        <section className="packet-sequence" aria-label="Archive page sequence">
          <div className="label-caps text-ink-soft">Archive sequence</div>
          {jumpTargets.map((t, i) => (
            <button
              key={`${t.leafIndex}-${i}`}
              type="button"
              onClick={() => setIndex(t.leafIndex)}
              className="idx-row"
              data-active={i === activeTargetIdx}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-medium">{t.label}</span>
              </div>
              <div className="text-ink-soft text-[0.62rem]">{t.sublabel}</div>
            </button>
          ))}
        </section>
      </div>
    </>
  );

  const contentPanel = (
    <>
      <div className="packet-panel__header packet-panel__header--compact">
        {backHref ? (
          <Link href={backHref} className="label-caps underline">
            ← {backLabel ?? "Back"}
          </Link>
        ) : null}
        <div className="font-bold text-lg leading-tight mt-1.5">
          {showDossierTree ? activeDossier?.title : "Nearby main sheets"}
        </div>
        <div className="label-caps text-ink-soft mt-1">Packet tree</div>
      </div>

      <div className="panel-scroll packet-panel__scroll">
        <section className="packet-tree packet-tree--diagram" aria-label="Research packet relationship tree">
          <div className="packet-tree__root">
            <span className="packet-tree__marker" aria-hidden />
            <div>
              <div className="packet-tree__title">
                {activeDossier?.title ?? contextTitle}
              </div>
              <div className="packet-tree__meta">
                {showDossierTree && activeDossier
                  ? `${formatAnchorType(activeDossier.anchorType)} / ${activeDossier.pageCount} pages`
                  : `${contextSubtitle} / previous and next main sheets`}
              </div>
            </div>
          </div>

          {showDossierTree && activeDossier ? (
            <div className="packet-tree__canvas">
              <span className="packet-tree__rail" aria-hidden />
              {activeDossier.pageSequence.map((page, pageIndex) => {
                const targetIndex = sIndex.get(page.surfaceId);
                const isActive =
                  page.surfaceId === activeSurface?.surfaceId &&
                  activeLeaf &&
                  dossierTypeMatchesLeaf(page.pageType, activeLeaf.type);

                return (
                  <button
                    key={page.pageId}
                    type="button"
                    className="packet-tree__item packet-tree__item--diagram"
                    data-active={isActive}
                    data-node-type={page.pageType}
                    disabled={targetIndex === undefined}
                    onClick={() => {
                      if (targetIndex !== undefined) setIndex(targetIndex);
                    }}
                    title={`${formatPageType(page.pageType)} / ${page.title ?? page.displayNumber ?? page.pageId}`}
                  >
                    <span className="packet-tree__node" aria-hidden />
                    <span className="packet-tree__body">
                      <span className="packet-tree__kicker">
                        {String(pageIndex + 1).padStart(2, "0")} / {formatPageType(page.pageType)}
                      </span>
                      <span className="packet-tree__label">
                        {page.title ?? page.displayNumber ?? page.pageId}
                      </span>
                      <span className="packet-tree__source">
                        {page.imageState ?? "IMG--"} / {page.sourceName ?? page.rightsState ?? "source pending"}
                      </span>
                      <span className="packet-tree__hover">
                        {pageRelationship(page.pageType)} · {page.rightsState ?? "rights pending"}
                        {page.sourceUrl ? " · source-linked" : ""}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="packet-tree__canvas">
              <span className="packet-tree__rail" aria-hidden />
              {nearbyMainSheetTargets.map(({ target, originalIndex }) => (
                <button
                  key={`${target.leafIndex}-${originalIndex}`}
                  type="button"
                  className="packet-tree__item packet-tree__item--diagram"
                  data-active={originalIndex === activeMainSheetIdx}
                  data-node-type="main_sheet"
                  onClick={() => setIndex(target.leafIndex)}
                  title={`${target.label} / ${target.sublabel}`}
                >
                  <span className="packet-tree__node" aria-hidden />
                  <span className="packet-tree__body">
                    <span className="packet-tree__kicker">
                      {String(originalIndex + 1).padStart(2, "0")} / main sheet
                    </span>
                    <span className="packet-tree__label">{target.label}</span>
                    <span className="packet-tree__source">{target.sublabel}</span>
                    <span className="packet-tree__hover">
                      Main sheet navigation only. Open Context for full archive sequence.
                    </span>
                  </span>
                </button>
              ))}
              <div className="packet-tree__empty">
                Packet grouping is pending; this view only shows nearby main sheets.
              </div>
            </div>
          )}
        </section>
      </div>
    </>
  );

  return (
    <ArchiveShell
      main={main}
      folderInk={folderInk}
      leftPanel={contentPanel}
      leftPanelLabel="Content"
      leftPanelSecondary={contextPanel}
      leftPanelSecondaryLabel="Context"
    />
  );
}

function IconAssistant() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden>
      <path d="M12 3v3" />
      <path d="M12 18v3" />
      <path d="M3 12h3" />
      <path d="M18 12h3" />
      <path d="M7.8 7.8l2.1 2.1" />
      <path d="M14.1 14.1l2.1 2.1" />
      <path d="M16.2 7.8l-2.1 2.1" />
      <path d="M9.9 14.1l-2.1 2.1" />
      <circle cx="12" cy="12" r="2.6" />
    </svg>
  );
}

function formatAnchorType(value: string) {
  return value.replace(/_/g, " ");
}

function formatScope(value: string) {
  return value.replace(/_/g, " ");
}

function formatPageType(value: string) {
  return value.replace(/_/g, " ");
}

function pageRelationship(value: string) {
  if (value === "main_sheet") return "anchor page";
  if (value === "subsheet") return "supporting sheet";
  if (value === "text_page") return "editorial reading page";
  if (value === "appendix") return "evidence appendix";
  if (value === "card") return "card record";
  if (value === "slip") return "source slip";
  if (value === "bookmark") return "navigation bookmark";
  return "packet node";
}

function dossierTypeMatchesLeaf(pageType: string, leafType: string) {
  if (pageType === "main_sheet") return leafType === "main";
  if (pageType === "subsheet") return leafType === "subsheet";
  if (pageType === "text_page") return leafType === "text";
  if (pageType === "appendix") return leafType === "appendix";
  if (pageType === "slip") return leafType === "slip";
  if (pageType === "card") return leafType === "main" || leafType === "subsheet";
  return false;
}
