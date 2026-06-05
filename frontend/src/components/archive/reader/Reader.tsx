"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { FolderTypeKey } from "@/types/archive";
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
  contextTitle,
  contextSubtitle,
  backHref,
  backLabel,
}: ReaderProps) {
  const [index, setIndex] = useState(
    Math.min(Math.max(initialIndex, 0), leaves.length - 1),
  );
  const [mode, setMode] = useState<"single" | "spread">("single");
  const [narrow, setNarrow] = useState(false);
  const [visualCheck, setVisualCheck] = useState<{
    ok: boolean;
    count: number;
    sample: string;
  }>({ ok: true, count: 0, sample: "visual/a11y ok" });

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 900px)");
    const update = () => setNarrow(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  const spread = mode === "spread" && !narrow;
  const step = spread ? 2 : 1;

  const next = useCallback(
    () => setIndex((i) => Math.min(i + step, leaves.length - 1)),
    [step, leaves.length],
  );
  const prev = useCallback(
    () => setIndex((i) => Math.max(i - step, 0)),
    [step],
  );

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

  const visible = spread
    ? [leaves[index], leaves[index + 1]].filter(Boolean)
    : [leaves[index]];

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
          if (
            style.overflow !== "visible" &&
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
          if (
            rect.left < leafRect.left - 1 ||
            rect.right > leafRect.right + 1 ||
            rect.top < leafRect.top - 1 ||
            rect.bottom > leafRect.bottom + 1
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
  }, [index, spread, visible.length]);

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
      <div className={`leaf-stage${spread ? " leaf-stage--spread" : ""}`}>
        {spread ? (
          <div className="leaf-spread">
            {visible[0] ? (
              <LeafFrame leaf={visible[0]} single={false} activeFolderId={activeFolderId} ctx={ctx} />
            ) : null}
            <div className="leaf-gutter" aria-hidden>
              <span className="binder-ring" />
              <span className="binder-ring" />
              <span className="binder-ring" />
              <span className="binder-ring" />
            </div>
            {visible[1] ? (
              <LeafFrame leaf={visible[1]} single={false} activeFolderId={activeFolderId} ctx={ctx} />
            ) : (
              <div className="leaf flex-1" />
            )}
          </div>
        ) : (
          <LeafFrame leaf={visible[0]} single activeFolderId={activeFolderId} ctx={ctx} />
        )}
      </div>

      <div className="page-turn">
        {/* Single / Spread toggle */}
        <button
          type="button"
          className="btn-turn"
          onClick={() => setMode((m) => (m === "single" ? "spread" : "single"))}
          disabled={narrow}
          aria-label={mode === "single" ? "Switch to spread view" : "Switch to single view"}
          title={mode === "single" ? "Spread" : "Single"}
        >
          {mode === "single" ? <IconSingle /> : <IconSpread />}
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
        title={visualCheck.sample}
        aria-live="polite"
      >
        <span>{visualCheck.ok ? "VIS OK" : `VIS ${visualCheck.count}`}</span>
      </div>
    </div>
  );

  const panel = (
    <>
      <div className="p-4 border-b border-ink">
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
        <div className="mt-3 flex items-center gap-1.5">
          <span className="label-caps text-ink-soft mr-1">view</span>
          <button
            type="button"
            onClick={() => setMode("single")}
            className={`btn-turn px-2 py-1 ${mode === "single" ? "bg-ink text-paper" : ""}`}
            disabled={narrow}
          >
            single
          </button>
          <button
            type="button"
            onClick={() => setMode("spread")}
            className={`btn-turn px-2 py-1 ${mode === "spread" ? "bg-ink text-paper" : ""}`}
            disabled={narrow}
          >
            spread
          </button>
        </div>
      </div>
      <div className="panel-scroll">
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
      </div>
    </>
  );

  return (
    <ArchiveShell
      main={main}
      folderInk={folderInk}
      panel={panel}
      panelLabel="Contents"
      hideWordmark={spread}
    />
  );
}

function IconSingle() {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" width="14" height="14">
      <rect x="5" y="3" width="10" height="14" />
    </svg>
  );
}

function IconSpread() {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" width="14" height="14">
      <rect x="1" y="3" width="8" height="14" />
      <rect x="11" y="3" width="8" height="14" />
    </svg>
  );
}
