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
  const [visualCheck, setVisualCheck] = useState<{
    ok: boolean;
    count: number;
    sample: string;
  }>({ ok: true, count: 0, sample: "visual/a11y ok" });

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

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const rootFontSize =
        Number.parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
      const fallbackLimits = {
        body: 0.72 * rootFontSize,
        metadata: 0.62 * rootFontSize,
        micro: 0.56 * rootFontSize,
      };
      const limitsForLeaf = (leaf: Element) => {
        const numberAttr = (name: string, fallback: number) => {
          const value = Number.parseFloat(leaf.getAttribute(name) ?? "");
          return Number.isFinite(value) ? value * rootFontSize : fallback;
        };
        return {
          body: numberAttr("data-min-body-rem", fallbackLimits.body),
          metadata: numberAttr("data-min-metadata-rem", fallbackLimits.metadata),
          micro: numberAttr("data-min-micro-rem", fallbackLimits.micro),
        };
      };
      const visibleElement = (el: Element) => {
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        return (
          rect.width > 0 &&
          rect.height > 0 &&
          style.visibility !== "hidden" &&
          style.display !== "none" &&
          Number(style.opacity) !== 0
        );
      };
      const scrollContainerFor = (el: Element) => {
        const container = el.closest(
          ".main-sheet, .sub-sheet, .archive-card, .source-slip, .appendix-sheet",
        );
        if (!container) return null;
        const style = getComputedStyle(container);
        const verticalScroll =
          style.overflowY === "auto" || style.overflowY === "scroll";
        return verticalScroll &&
          (container as HTMLElement).scrollHeight >
            (container as HTMLElement).clientHeight + 2
          ? container
          : null;
      };
      const intersects = (a: DOMRect, b: DOMRect) =>
        a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
      const textOf = (el: Element) => (el.textContent || "").replace(/\s+/g, " ").trim();
      const roleFor = (el: Element): keyof typeof fallbackLimits | null => {
        const tag = el.tagName;
        const className = String((el as HTMLElement).className || "");
        if (
          /label|kicker|meta|footer|badge|code|state|accession|marker|caption|context|source|rights|row|ledger/i.test(
            className,
          )
        ) {
          return "micro";
        }
        if (["TD", "TH", "DT", "FIGCAPTION", "A", "BUTTON", "SUMMARY"].includes(tag)) {
          return "metadata";
        }
        if (["P", "LI", "BLOCKQUOTE", "DD"].includes(tag)) return "body";
        return null;
      };

      const errors: string[] = [];
      const leafs = Array.from(document.querySelectorAll(".leaf")).filter(visibleElement);
      for (const leaf of leafs) {
        const leafRect = leaf.getBoundingClientRect();
        const limits = limitsForLeaf(leaf);
        const overflowPolicy = leaf.getAttribute("data-overflow-policy") ?? "none";
        const level = leaf.getAttribute("data-level") ?? "unknown";
        const clippedContainers = Array.from(
          leaf.querySelectorAll(
            ".reading-note__card, .main-sheet, .appendix-sheet, .sub-sheet, .text-page, .archive-card, .source-slip",
          ),
        ).filter(visibleElement);
        for (const el of clippedContainers) {
          const style = getComputedStyle(el);
          const verticalScroll =
            style.overflowY === "auto" || style.overflowY === "scroll";
          if (
            style.overflow !== "visible" &&
            !verticalScroll &&
            ((el as HTMLElement).scrollHeight > (el as HTMLElement).clientHeight + 2 ||
              (el as HTMLElement).scrollWidth > (el as HTMLElement).clientWidth + 2)
          ) {
            errors.push(`overflow contract failed (${level}/${overflowPolicy}): ${el.className}`);
          }
        }
        const textNodes = Array.from(
          leaf.querySelectorAll("p, h1, h2, h3, h4, li, dt, dd, th, td, span, strong, em, a, figcaption"),
        ).filter((el) => visibleElement(el) && textOf(el));

        for (const el of textNodes) {
          const rect = el.getBoundingClientRect();
          const style = getComputedStyle(el);
          const label = textOf(el).slice(0, 56);
          const scrollContainer = scrollContainerFor(el);
          if (
            rect.left < leafRect.left - 1 ||
            rect.right > leafRect.right + 1 ||
            (!scrollContainer &&
              (rect.top < leafRect.top - 1 || rect.bottom > leafRect.bottom + 1))
          ) {
            errors.push(`text overflow: ${label}`);
          }

          const role = roleFor(el);
          const size = Number.parseFloat(style.fontSize);
          if (role && Number.isFinite(size) && size + 0.01 < limits[role]) {
            errors.push(`font below ${role} min: ${label}`);
          }

          if (
            /[\u3040-\u30ff\u3400-\u9fff]/.test(label) &&
            (style.wordBreak === "break-all" ||
              style.writingMode !== "horizontal-tb" ||
              (rect.width < 42 && label.length > 3))
          ) {
            errors.push(`CJK broken: ${label}`);
          }
        }

        if (
          leaf.getAttribute("data-image-state") === "IMG04" ||
          leaf.getAttribute("data-level") === "IMG04"
        ) {
          const img04Frame = Array.from(
            leaf.querySelectorAll(".image-bay, .main-sheet-plate, .main-sheet-plate__frame, .main-sheet-plate__empty, img"),
          ).find(visibleElement);
          if (img04Frame) errors.push(`${level} image frame contract failed`);
        }
      }

      const pageTurn = document.querySelector(".page-turn");
      if (pageTurn && visibleElement(pageTurn)) {
        const navRect = pageTurn.getBoundingClientRect();
        for (const leaf of leafs) {
          if (intersects(navRect, leaf.getBoundingClientRect())) {
            errors.push("page navigation overlaps leaf");
            break;
          }
        }
      }

      setVisualCheck({
        ok: errors.length === 0,
        count: errors.length,
        sample: errors[0] ?? "visual/a11y ok",
      });
    }, 160);
    return () => window.clearTimeout(timer);
  }, [index, visible.length]);

  const atStart = index <= 0;
  const atEnd = index >= leaves.length - 1;

  const activeTargetIdx = useMemo(() => {
    let active = 0;
    jumpTargets.forEach((t, i) => {
      if (t.leafIndex <= index) active = i;
    });
    return active;
  }, [jumpTargets, index]);

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
          aria-label="Open assistant"
          title="Assistant"
        >
          <IconAssistant />
          <span>Assistant</span>
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
      <div
        className={`visual-check ${visualCheck.ok ? "visual-check--ok" : "visual-check--fail"}`}
        data-release-note="remove-before-launch"
        title={`Pre-release QA marker: ${visualCheck.sample}`}
        aria-live="polite"
      >
        <span>{visualCheck.ok ? "VIS OK" : `VIS ${visualCheck.count}`}</span>
      </div>
    </div>
  );

  const packetPanel = (
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
          <div className="label-caps text-ink-soft">Research packet anchor</div>
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

        <section className="packet-tree" aria-label="Research packet relationship tree">
          <div className="packet-tree__root">
            <span className="packet-tree__marker" aria-hidden />
            <div>
              <div className="packet-tree__title">
                {activeDossier?.title ?? contextTitle}
              </div>
              <div className="packet-tree__meta">
                {activeSurface?.dateText ?? contextSubtitle}
              </div>
            </div>
          </div>

          {activeDossier?.pageSequence.length ? (
            <div className="packet-tree__branch">
              {activeDossier.pageSequence.map((page) => {
                const targetIndex = sIndex.get(page.surfaceId);
                const isActive =
                  page.surfaceId === activeSurface?.surfaceId &&
                  activeLeaf &&
                  dossierTypeMatchesLeaf(page.pageType, activeLeaf.type);

                return (
                  <button
                    key={page.pageId}
                    type="button"
                    className="packet-tree__item"
                    data-active={isActive}
                    disabled={targetIndex === undefined}
                    onClick={() => {
                      if (targetIndex !== undefined) setIndex(targetIndex);
                    }}
                  >
                    <span className="packet-tree__node" aria-hidden />
                    <span className="packet-tree__body">
                      <span className="packet-tree__kicker">
                        {formatPageType(page.pageType)}
                        {page.imageState ? ` / ${page.imageState}` : ""}
                      </span>
                      <span className="packet-tree__label">
                        {page.title ?? page.displayNumber ?? page.pageId}
                      </span>
                      <span className="packet-tree__source">
                        {page.sourceName ?? page.rightsState ?? "source pending"}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="packet-tree__empty">
              {activeSurface
                ? "Dossier grouping is pending; use the archive sequence below as the current page structure."
                : "Folder register pages are not yet grouped into a packet sequence."}
            </div>
          )}
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

  return (
    <ArchiveShell
      main={main}
      folderInk={folderInk}
      leftPanel={packetPanel}
      leftPanelLabel="Content"
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

function dossierTypeMatchesLeaf(pageType: string, leafType: string) {
  if (pageType === "main_sheet") return leafType === "main";
  if (pageType === "subsheet") return leafType === "subsheet";
  if (pageType === "text_page") return leafType === "text";
  if (pageType === "appendix") return leafType === "appendix";
  if (pageType === "slip") return leafType === "slip";
  if (pageType === "card") return leafType === "main" || leafType === "subsheet";
  return false;
}
