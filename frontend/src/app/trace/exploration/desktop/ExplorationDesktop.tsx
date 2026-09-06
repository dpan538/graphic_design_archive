"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import SiteNav from "@/components/site/SiteNav";
import SharedDock, { PanelGlyph, type DockTool } from "../../_shared/Dock";
import type { ExplorationStartingPointDto, ExplorationViewAction, ExplorationViewDto } from "@/features/trace-v49/exploration-view/types";
import { DESCRIPTION, DESCRIPTION_CLOSE, EXPORT_FAILED, FAILED, STALE } from "../lib/content";
import DescriptionDrawer from "./DescriptionDrawer";
import ExplorationRail from "./ExplorationRail";
import InquiryDrawer, { type InquiryItem } from "./InquiryDrawer";
import Stage from "./Stage";
import styles from "./ExplorationDesktop.module.css";

/* Exploration, desktop (FRONTEND_DESIGN_DECISION.md §7i): the rail at the
   left — starting point, complexity, another view, export, the Open
   Inquiry entry — the view as the body, and one right drawer: DESCRIPTION
   (open when a view is first generated; once the reader closes it, the
   ordinary More / Less / Another view transitions leave it closed), or an
   inquiry. Every change is a request to the view
   API, which moves only along V2's own transitions; the page never
   derives a state, a position or an association of its own. Requests are
   epoch-guarded: a late response never overwrites a newer state. The URL
   carries map · state · template · variant, so a view can be reopened. */

export interface ExplorationDesktopProps {
  readonly initialView: ExplorationViewDto;
  readonly startingPoints: readonly ExplorationStartingPointDto[];
  readonly inquiries: readonly InquiryItem[];
}

type Pending = "START" | ExplorationViewAction | "EXPORT" | null;
type Drawer = "description" | "inquiry" | null;

const API = "/api/trace/exploration-view/v1";

export default function ExplorationDesktop({ initialView, startingPoints, inquiries }: ExplorationDesktopProps) {
  const [view, setView] = useState<ExplorationViewDto>(initialView);
  const [pending, setPending] = useState<Pending>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [drawer, setDrawer] = useState<Drawer>("description");
  const [inquiryIndex, setInquiryIndex] = useState<number | null>(null);
  const [choosing, setChoosing] = useState(false);
  /* the reader closed the description on purpose: transitions respect it */
  const closedByReader = useRef(false);
  const epoch = useRef(0);
  const sourceBoundary = useRef<HTMLParagraphElement | null>(null);

  /* the URL follows the view */
  useEffect(() => {
    const url = new URL(window.location.href);
    url.search = "";
    url.searchParams.set("map", view.restore.map_id);
    url.searchParams.set("state", view.restore.state_id);
    url.searchParams.set("template", view.restore.template_id);
    url.searchParams.set("variant", String(view.restore.variant_id));
    window.history.replaceState(window.history.state, "", url.toString());
  }, [view.restore]);

  const request = useCallback(async (kind: Exclude<Pending, null | "EXPORT">, path: string, body: unknown) => {
    const mine = ++epoch.current;
    setPending(kind);
    setNotice(null);
    try {
      const response = await fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(body), cache: "no-store" });
      const payload = await response.json().catch(() => null) as ExplorationViewDto | { code?: string; message?: string } | null;
      if (mine !== epoch.current) return; /* a newer request took over */
      if (response.ok && payload && "restore" in payload) {
        setView(payload);
        return;
      }
      const code = payload && "code" in payload ? payload.code : undefined;
      if (code === "STALE_EXPLORATION_STATE") {
        /* the state we hold is not the map's any more: reload the map's current view */
        const fresh = await fetch(`${API}/views/${encodeURIComponent(view.restore.map_id)}?state=${encodeURIComponent(view.restore.state_id)}&template=${view.restore.template_id}&variant=${view.restore.variant_id}`, { cache: "no-store" });
        const freshPayload = await fresh.json().catch(() => null) as ExplorationViewDto | null;
        if (mine !== epoch.current) return;
        if (fresh.ok && freshPayload && "restore" in freshPayload) setView(freshPayload);
        setNotice(STALE);
        return;
      }
      setNotice(payload && "message" in payload && typeof payload.message === "string" ? payload.message : FAILED);
    } catch {
      if (mine === epoch.current) setNotice(FAILED);
    } finally {
      if (mine === epoch.current) setPending(null);
    }
  }, [view.restore]);

  const start = useCallback((vocabularyId: string) => {
    void request("START", "/views", { vocabulary_id: vocabularyId });
  }, [request]);

  const act = useCallback((action: ExplorationViewAction) => {
    void request(action, `/views/${encodeURIComponent(view.restore.map_id)}/actions`, {
      action,
      expected_state_hash: view.restore.state_hash,
      template_id: view.restore.template_id,
      variant_id: view.restore.variant_id,
    });
  }, [request, view.restore]);

  const exportPng = useCallback(async () => {
    const mine = ++epoch.current;
    setPending("EXPORT");
    setNotice(null);
    try {
      const response = await fetch(`${API}/exports/png`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          map_id: view.restore.map_id,
          state_hash: view.restore.state_hash,
          composition_id: view.map.composition.composition_id,
          template_id: view.restore.template_id,
          variant_id: view.restore.variant_id,
        }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error(EXPORT_FAILED);
      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") ?? "";
      const name = /filename="([^"]+)"/u.exec(disposition)?.[1] ?? "mgda-exploration.png";
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = name;
      anchor.rel = "noopener";
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 2_000);
    } catch {
      if (mine === epoch.current) setNotice(EXPORT_FAILED);
    } finally {
      if (mine === epoch.current) setPending(null);
    }
  }, [view]);

  const openInquiry = useCallback(() => {
    setDrawer((current) => (current === "inquiry" ? (closedByReader.current ? null : "description") : "inquiry"));
  }, []);
  const toggleDescription = useCallback(() => {
    setDrawer((current) => {
      if (current === "description") { closedByReader.current = true; return null; }
      closedByReader.current = false;
      return "description";
    });
  }, []);
  const closeDescription = useCallback(() => {
    closedByReader.current = true;
    setDrawer(null);
  }, []);

  /* Escape closes the drawer */
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (choosing) setChoosing(false);
      else if (drawer === "description") closeDescription();
      else if (drawer) setDrawer(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawer, choosing, closeDescription]);

  const tools = useMemo<DockTool[]>(() => [
    {
      id: "description",
      revealOpen: DESCRIPTION_CLOSE,
      revealClosed: DESCRIPTION,
      open: drawer === "description",
      controls: "exploration-drawer",
      onClick: toggleDescription,
      glyph: <PanelGlyph open={drawer === "description"} />,
    },
  ], [drawer, toggleDescription]);

  const locked = pending !== null;

  return (
    <div className={styles.page}>
      <a href="#main" className="skip-link">Skip to content</a>
      <SiteNav active="trace" revealTone="light" />
      <SharedDock active="exploration" tools={tools} toolsLabel="View tools" />
      <div className={styles.grain} aria-hidden="true" />

      <main id="main" className={styles.main} data-drawer={drawer ?? "closed"}>
        <div className={styles.rail}>
          <ExplorationRail
            view={view}
            startingPoints={startingPoints}
            inquiryCount={inquiries.length}
            inquiryOpen={drawer === "inquiry"}
            choosing={choosing}
            pending={pending}
            locked={locked}
            onChoosing={setChoosing}
            onStart={start}
            onAction={act}
            onExport={() => void exportPng()}
            onOpenInquiry={openInquiry}
          />
        </div>

        <section className={styles.centre} aria-label="Exploration view">
          <Stage view={view} pending={pending} notice={notice} />
        </section>

        {drawer ? (
          <aside id="exploration-drawer" className={styles.drawer} aria-label={drawer === "description" ? DESCRIPTION : "Open inquiry"}>
            {drawer === "description" ? (
              <DescriptionDrawer view={view} onClose={closeDescription} />
            ) : (
              <InquiryDrawer
                items={inquiries}
                selected={inquiryIndex}
                onSelect={setInquiryIndex}
                onClose={() => setDrawer(closedByReader.current ? null : "description")}
                sourceBoundaryRef={sourceBoundary}
                onSuggestion={(actionId) => {
                  if (actionId === "RETURN_TO_EXPLORATION" || actionId === "RETURN_TO_VALIDATED_EXPLORATION") setDrawer(null);
                  if (actionId === "REVIEW_SOURCE_BOUNDARY") sourceBoundary.current?.focus();
                }}
              />
            )}
          </aside>
        ) : null}
      </main>
    </div>
  );
}
