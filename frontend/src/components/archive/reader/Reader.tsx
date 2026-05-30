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
