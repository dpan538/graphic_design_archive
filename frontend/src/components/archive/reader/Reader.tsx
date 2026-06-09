"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import Link from "next/link";
import type { FolderTypeKey, ResearchDossier, Surface } from "@/types/archive";
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
  const [contextOpen, setContextOpen] = useState(false);
  const [contextView, setContextView] = useState<ContextView>("relation");
  const [selectedContextId, setSelectedContextId] = useState("active");

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

  useEffect(() => {
    setSelectedContextId("active");
  }, [activeSurface?.surfaceId, activeLeaf?.id]);

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

  const contextNodes = useMemo(
    () =>
      buildContextNodes({
        activeSurface,
        activeDossier,
        activeLeaf,
        activeTargetIdx,
        contextTitle,
        contextSubtitle,
        jumpTargets,
        leaves,
        sIndex,
      }),
    [
      activeDossier,
      activeLeaf,
      activeSurface,
      activeTargetIdx,
      contextSubtitle,
      contextTitle,
      jumpTargets,
      leaves,
      sIndex,
    ],
  );
  const contextEdges = useMemo(() => buildContextEdges(contextNodes), [contextNodes]);
  const selectedContextNode =
    contextNodes.find((node) => node.id === selectedContextId) ?? contextNodes[0];

  const focusIds = useMemo(() => {
    const ids = new Set(["active", selectedContextNode?.id ?? "active"]);
    for (const edge of contextEdges) {
      if (edge.from === selectedContextNode?.id) ids.add(edge.to);
      if (edge.to === selectedContextNode?.id) ids.add(edge.from);
    }
    return ids;
  }, [contextEdges, selectedContextNode]);

  const openContextNode = useCallback(
    (node: ContextNode) => {
      setSelectedContextId(node.id);
      if (typeof node.leafIndex === "number") {
        setIndex(node.leafIndex);
      }
    },
    [],
  );

  const main = (
    <div className={`relative flex-1 min-h-0 flex flex-col reader-main ${contextOpen ? "reader-main--context-open" : ""}`}>
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

  const contentPanel = (
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

  const contextOverlay = (
    <section
      className="reader-context-overlay"
      data-view={contextView}
      aria-label="Surface context relationship layer"
    >
      <div className="reader-context-head">
        <div className="reader-context-eyebrow">Context / relation layer</div>
        <h2>{contextView === "map" ? "Geographic map" : "Surface relation"}</h2>
        <div className="reader-context-meta">
          <span>Mode: {contextView}</span>
        </div>
      </div>

      <button
        type="button"
        className="reader-context-tool reader-context-tool--close"
        aria-label="Close context"
        onClick={() => setContextOpen(false)}
      >
        <IconClose />
      </button>

      <div className="reader-context-switch" aria-label="Context view">
        <button
          type="button"
          className="reader-context-tool"
          data-active={contextView === "map"}
          aria-label="Map view"
          onClick={() => setContextView("map")}
        >
          <IconMap />
        </button>
        <button
          type="button"
          className="reader-context-tool"
          data-active={contextView === "relation"}
          aria-label="Surface relation view"
          onClick={() => setContextView("relation")}
        >
          <IconRelation />
        </button>
      </div>

      <div className="reader-context-canvas">
        {contextView === "map" ? (
          <ContextMap
            nodes={contextNodes}
            edges={contextEdges}
            selectedId={selectedContextNode?.id ?? "active"}
            onPreview={(node) => setSelectedContextId(node.id)}
            onSelect={openContextNode}
          />
        ) : (
          <ContextRelation
            nodes={contextNodes}
            edges={contextEdges}
            focusIds={focusIds}
            selectedId={selectedContextNode?.id ?? "active"}
            onSelect={openContextNode}
            onPreview={(node) => setSelectedContextId(node.id)}
          />
        )}
      </div>

      <dl className="reader-context-readout" aria-live="polite">
        <dt>node</dt>
        <dd>{selectedContextNode ? `${selectedContextNode.kind}: ${selectedContextNode.title}` : "surface context"}</dd>
        <dt>basis</dt>
        <dd>{selectedContextNode?.meta ?? contextSubtitle}</dd>
        <dt>evidence</dt>
        <dd>{selectedContextNode?.evidence ?? "Select a context node to inspect relation evidence."}</dd>
      </dl>
    </section>
  );

  return (
    <ArchiveShell
      main={main}
      folderInk={folderInk}
      leftPanel={contentPanel}
      leftPanelLabel="Content"
      contextOverlay={contextOverlay}
      contextOverlayOpen={contextOpen}
      onContextOverlayOpenChange={setContextOpen}
      contextOverlayLabel="Context"
    />
  );
}

type ContextView = "relation" | "map";
type ContextKind = "surface" | "source" | "rights" | "image" | "date" | "folder" | "page";
type ContextRole = "active" | "core" | "support";
type Point = [number, number];

interface GeoPoint {
  lat: number;
  lon: number;
}

interface ContextNode {
  id: string;
  kind: ContextKind;
  role: ContextRole;
  label: string;
  title: string;
  meta: string;
  evidence: string;
  relation: Point;
  geo?: GeoPoint;
  geoInferred?: boolean;
  mapLabel?: string;
  leafIndex?: number;
}

interface ContextEdge {
  from: string;
  to: string;
  type: "core" | "sequence" | "folder" | "page" | "support";
}

function ContextRelation({
  nodes,
  edges,
  focusIds,
  selectedId,
  onPreview,
  onSelect,
}: {
  nodes: ContextNode[];
  edges: ContextEdge[];
  focusIds: Set<string>;
  selectedId: string;
  onPreview: (node: ContextNode) => void;
  onSelect: (node: ContextNode) => void;
}) {
  return (
    <div className="reader-context-relation">
      <svg className="reader-context-edges" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
        {edges.map((edge) => {
          const from = nodes.find((node) => node.id === edge.from);
          const to = nodes.find((node) => node.id === edge.to);
          if (!from || !to) return null;
          const highlighted = edge.from === selectedId || edge.to === selectedId;
          const dimmed = !highlighted && selectedId !== "active";
          return (
            <path
              key={`${edge.from}-${edge.to}-${edge.type}`}
              className={`reader-context-edge reader-context-edge--${edge.type} ${highlighted ? "is-highlighted" : ""} ${dimmed ? "is-dimmed" : ""}`}
              d={relationPath(from.relation, to.relation)}
            />
          );
        })}
      </svg>
      {nodes.map((node) => {
        const focused = focusIds.has(node.id);
        const selected = node.id === selectedId;
        return (
          <button
            key={node.id}
            type="button"
            className={`reader-context-node reader-context-node--${node.role} reader-context-node--${node.kind} ${selected ? "is-selected" : ""} ${focused ? "is-focused" : "is-dimmed"}`}
            style={pointStyle(node.relation)}
            onMouseEnter={() => onPreview(node)}
            onFocus={() => onPreview(node)}
            onClick={() => onSelect(node)}
          >
            <span className="reader-context-node__kind">[{node.label}]</span>
            <span className="reader-context-node__title">{node.title}</span>
            <span className="reader-context-node__meta">{node.meta}</span>
          </button>
        );
      })}
      <div className="reader-context-field-note">Hover node for evidence</div>
    </div>
  );
}

function ContextMap({
  nodes,
  edges,
  selectedId,
  onPreview,
  onSelect,
}: {
  nodes: ContextNode[];
  edges: ContextEdge[];
  selectedId: string;
  onPreview: (node: ContextNode) => void;
  onSelect: (node: ContextNode) => void;
}) {
  const geoNodes = nodes.filter((node) => node.geo);
  const selectedNode = geoNodes.find((node) => node.id === selectedId) ?? geoNodes[0];
  const detailPoint = selectedNode?.geo ? mercatorTilePoint(selectedNode.geo, DETAIL_MAP) : null;
  return (
    <div className="reader-context-map">
      <div className="reader-context-map-pane reader-context-map-pane--detail">
        <TileGrid config={DETAIL_MAP} className="reader-context-tile-grid--detail" />
        {detailPoint ? (
          <span
            className="reader-context-map-dot reader-context-map-dot--active"
            style={pointStyle(detailPoint)}
            aria-hidden
          />
        ) : null}
      </div>
      <div className="reader-context-map-pane reader-context-map-pane--world">
        <TileGrid config={WORLD_MAP} className="reader-context-tile-grid--world" />
        <svg className="reader-context-map-edges" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
          {edges.map((edge) => {
            const from = geoNodes.find((node) => node.id === edge.from);
            const to = geoNodes.find((node) => node.id === edge.to);
            if (!from?.geo || !to?.geo) return null;
            const a = worldPoint(from.geo);
            const b = worldPoint(to.geo);
            return (
              <path
                key={`${edge.from}-${edge.to}-${edge.type}`}
                d={mapPath(a, b)}
                className={edge.from === selectedId || edge.to === selectedId ? "is-highlighted" : ""}
              />
            );
          })}
        </svg>
        {geoNodes.map((node) => {
          const point = node.geo ? worldPoint(node.geo) : null;
          if (!point) return null;
          const active = node.id === selectedNode?.id;
          return (
            <button
              key={node.id}
              type="button"
              className={`reader-context-map-pin ${active ? "is-active" : ""} ${node.geoInferred ? "is-inferred" : ""}`}
              style={pointStyle(point)}
              aria-label={`${node.title} location`}
              data-label={node.mapLabel ?? node.title}
              onMouseEnter={() => onPreview(node)}
              onFocus={() => onPreview(node)}
              onClick={() => onSelect(node)}
            />
          );
        })}
        <div className="reader-context-map-attribution">© OpenStreetMap contributors</div>
      </div>
      <div className="reader-context-map-note">
        <span>Basis</span>
        <span>exact, folder, or inferred regional coordinates</span>
        <span>Read</span>
        <span>blue marker is active; small rings are related locations</span>
      </div>
      <div className="reader-context-map-coordinate">
        {selectedNode?.mapLabel ?? selectedNode?.title ?? "mapped surface"}
        {selectedNode?.geo ? ` ${selectedNode.geo.lat.toFixed(5)}, ${selectedNode.geo.lon.toFixed(5)}` : ""}
      </div>
    </div>
  );
}

function TileGrid({ config, className }: { config: TileConfig; className: string }) {
  const tiles = [];
  for (let row = 0; row < config.rows; row += 1) {
    for (let col = 0; col < config.cols; col += 1) {
      const x = config.startX + col;
      const y = config.startY + row;
      tiles.push(
        <img
          key={`${config.z}-${x}-${y}`}
          src={`https://tile.openstreetmap.org/${config.z}/${x}/${y}.png`}
          alt=""
          loading="eager"
          decoding="async"
        />,
      );
    }
  }
  return <div className={`reader-context-tile-grid ${className}`}>{tiles}</div>;
}

function IconClose() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden>
      <line x1="6" y1="6" x2="18" y2="18" />
      <line x1="18" y1="6" x2="6" y2="18" />
    </svg>
  );
}

function IconMap() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden>
      <path d="M4 6l5-2 6 2 5-2v16l-5 2-6-2-5 2z" />
      <line x1="9" y1="4" x2="9" y2="20" />
      <line x1="15" y1="6" x2="15" y2="22" />
    </svg>
  );
}

function IconRelation() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden>
      <circle cx="6" cy="5" r="2" />
      <circle cx="17" cy="12" r="2" />
      <circle cx="17" cy="19" r="2" />
      <path d="M8 5h3v14h4" />
      <path d="M11 12h4" />
    </svg>
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

interface BuildContextNodesInput {
  activeSurface?: Surface;
  activeDossier?: ResearchDossier;
  activeLeaf?: Leaf;
  activeTargetIdx: number;
  contextTitle: string;
  contextSubtitle: string;
  jumpTargets: JumpTarget[];
  leaves: Leaf[];
  sIndex: Map<string, number>;
}

function buildContextNodes({
  activeSurface,
  activeDossier,
  activeLeaf,
  activeTargetIdx,
  contextTitle,
  contextSubtitle,
  jumpTargets,
  leaves,
  sIndex,
}: BuildContextNodesInput): ContextNode[] {
  const activeGeo = activeSurface ? geoContextForSurface(activeSurface) : undefined;
  const nodes: ContextNode[] = [
    {
      id: "active",
      kind: "surface",
      role: "active",
      label: "SURF",
      title: activeSurface?.title ?? contextTitle,
      meta: activeSurface?.dateText ?? contextSubtitle,
      evidence: activeSurface
        ? `Current ${activeLeaf?.type ?? "surface"} leaf. Relation mode joins source, rights, image state, folders, date, sequence and dossier context.${activeGeo?.inferred ? " Map position uses broader inferred geographic context." : ""}`
        : "Current register leaf. Surface-level context appears once a surface leaf is active.",
      relation: [28, 49],
      geo: activeGeo?.point,
      geoInferred: activeGeo?.inferred,
      mapLabel: activeGeo?.label ?? contextTitle,
      leafIndex: activeSurface ? sIndex.get(activeSurface.surfaceId) : undefined,
    },
  ];

  if (activeSurface) {
    nodes.push(
      {
        id: "source",
        kind: "source",
        role: "core",
        label: "SRC",
        title: "Source registry",
        meta: activeSurface.sourceName || "source pending",
        evidence: activeSurface.sourceUrl
          ? `Source URL is available for ${activeSurface.sourceName}.`
          : "Source registry exists, but a source URL is not available.",
        relation: [43, 18],
      },
      {
        id: "rights",
        kind: "rights",
        role: "core",
        label: "RGT",
        title: "Rights display state",
        meta: activeSurface.rights.state || activeSurface.rights.displayPolicy,
        evidence: activeSurface.rights.label || activeSurface.rights.displayPolicy,
        relation: [43, 32],
      },
      {
        id: "image",
        kind: "image",
        role: "core",
        label: "IMG",
        title: `${activeSurface.image.state} ${activeSurface.image.hasImageFrame ? "available" : "record"}`,
        meta: activeSurface.image.licenseLabel ?? activeSurface.image.credit ?? "image evidence",
        evidence: activeSurface.image.url
          ? "Image URL is available; the reader can render an image frame."
          : "No display image URL is currently available for this surface.",
        relation: [43, 46],
      },
      {
        id: "date",
        kind: "date",
        role: "core",
        label: "DAT",
        title: activeSurface.dateText || "undated",
        meta: dateSpan(activeSurface),
        evidence: "Date evidence anchors the surface in the archive chronology.",
        relation: [43, 60],
      },
    );

    const regionFolder = activeSurface.folders.find((folder) => folder.type === "region");
    const supportFolder =
      activeSurface.folders.find((folder) => folder.type !== "region") ??
      activeSurface.folders[0];
    if (regionFolder) {
      const regionGeo = geoForText(regionFolder.title) ?? INFERRED_GLOBAL_GEO;
      nodes.push({
        id: "folder-region",
        kind: "folder",
        role: "core",
        label: "FOL",
        title: regionFolder.title,
        meta: "region folder",
        evidence: "Folder membership is resolved from the active surface record.",
        relation: [43, 74],
        geo: regionGeo.point,
        geoInferred: regionGeo.inferred,
        mapLabel: `${regionFolder.title} / folder`,
      });
    }
    if (supportFolder && supportFolder.folderId !== regionFolder?.folderId) {
      nodes.push({
        id: "folder-support",
        kind: "folder",
        role: "support",
        label: "FOL",
        title: supportFolder.title,
        meta: `${supportFolder.type} folder`,
        evidence: "Secondary folder membership gives the surface a thematic or medium context.",
        relation: [66, 74],
      });
    }
  }

  const previousTarget = jumpTargets[Math.max(0, activeTargetIdx - 1)];
  const nextTarget = jumpTargets[Math.min(jumpTargets.length - 1, activeTargetIdx + 1)];
  if (previousTarget && previousTarget.leafIndex !== jumpTargets[activeTargetIdx]?.leafIndex) {
    nodes.push(sequenceNode("near-prev", "SEQ -1", "Previous", previousTarget, leaves, [28, 72]));
  }
  if (nextTarget && nextTarget.leafIndex !== jumpTargets[activeTargetIdx]?.leafIndex) {
    nodes.push(sequenceNode("near-next", "SEQ +1", "Next", nextTarget, leaves, [28, 28]));
  }

  if (activeDossier?.pageSequence.length) {
    const pagePositions: Point[] = [
      [70, 24],
      [78, 36],
      [78, 48],
    ];
    activeDossier.pageSequence.slice(0, 3).forEach((page, pageIndex) => {
      nodes.push({
        id: `dossier-${pageIndex}`,
        kind: "page",
        role: "support",
        label: `P${String(pageIndex + 1).padStart(2, "0")}`,
        title: page.title ?? page.displayNumber ?? page.pageId,
        meta: page.pageType.replace(/_/g, " "),
        evidence: page.sourceName || page.rightsState || "Dossier page in the active research packet.",
        relation: pagePositions[pageIndex],
        leafIndex: sIndex.get(page.surfaceId),
      });
    });
  }

  return nodes;
}

function buildContextEdges(nodes: ContextNode[]): ContextEdge[] {
  const ids = new Set(nodes.map((node) => node.id));
  const edges: ContextEdge[] = [];
  const push = (from: string, to: string, type: ContextEdge["type"]) => {
    if (ids.has(from) && ids.has(to)) edges.push({ from, to, type });
  };
  push("active", "source", "core");
  push("active", "rights", "core");
  push("active", "image", "core");
  push("active", "date", "core");
  push("active", "folder-region", "folder");
  push("folder-region", "folder-support", "support");
  push("near-prev", "active", "sequence");
  push("active", "near-next", "sequence");
  push("active", "dossier-0", "page");
  push("dossier-0", "dossier-1", "page");
  push("dossier-1", "dossier-2", "page");
  return edges;
}

function sequenceNode(
  id: string,
  label: string,
  direction: string,
  target: JumpTarget,
  leaves: Leaf[],
  relation: Point,
): ContextNode {
  const surface = leaves[target.leafIndex]?.surface;
  const geo = surface ? geoContextForSurface(surface) : undefined;
  return {
    id,
    kind: "surface",
    role: "support",
    label,
    title: target.label,
    meta: target.sublabel || direction,
    evidence: `${direction} navigation target in the current archive sequence.`,
    relation,
    geo: geo?.point,
    geoInferred: geo?.inferred,
    mapLabel: geo?.label ?? target.label,
    leafIndex: target.leafIndex,
  };
}

function dateSpan(surface: Surface) {
  if (surface.dateStart && surface.dateEnd && surface.dateStart !== surface.dateEnd) {
    return `${surface.dateStart}-${surface.dateEnd}`;
  }
  return surface.dateText || String(surface.dateStart ?? surface.dateEnd ?? "date pending");
}

const PLACE_COORDS: Array<[RegExp, GeoPoint]> = [
  [/munich|münchen/i, { lat: 48.1351, lon: 11.582 }],
  [/ulm/i, { lat: 48.4011, lon: 9.9876 }],
  [/zurich|zürich|switzerland|swiss/i, { lat: 47.3769, lon: 8.5417 }],
  [/amsterdam|netherlands|dutch/i, { lat: 52.3676, lon: 4.9041 }],
  [/tokyo|japan/i, { lat: 35.6762, lon: 139.6503 }],
  [/mexico city|mexico/i, { lat: 19.4326, lon: -99.1332 }],
  [/new york/i, { lat: 40.7128, lon: -74.006 }],
  [/chicago/i, { lat: 41.8781, lon: -87.6298 }],
  [/los angeles/i, { lat: 34.0522, lon: -118.2437 }],
  [/london|united kingdom|britain|uk/i, { lat: 51.5074, lon: -0.1278 }],
  [/paris|france/i, { lat: 48.8566, lon: 2.3522 }],
  [/berlin|germany|europe/i, { lat: 51.1657, lon: 10.4515 }],
  [/milan|italy/i, { lat: 45.4642, lon: 9.19 }],
  [/moscow|russia/i, { lat: 55.7558, lon: 37.6173 }],
  [/beijing|china/i, { lat: 39.9042, lon: 116.4074 }],
  [/hong kong/i, { lat: 22.3193, lon: 114.1694 }],
  [/seoul|korea/i, { lat: 37.5665, lon: 126.978 }],
  [/sydney|australia/i, { lat: -33.8688, lon: 151.2093 }],
  [/brazil|são paulo|sao paulo/i, { lat: -23.5558, lon: -46.6396 }],
  [/south africa|johannesburg/i, { lat: -26.2041, lon: 28.0473 }],
  [/india|delhi/i, { lat: 28.6139, lon: 77.209 }],
];

interface GeoResolution {
  point: GeoPoint;
  label: string;
  inferred: boolean;
}

const INFERRED_GLOBAL_GEO: GeoResolution = {
  point: { lat: 20, lon: 0 },
  label: "Global / inferred context",
  inferred: true,
};

function geoContextForSurface(surface: Surface): GeoResolution {
  const exactText = [surface.placeText, surface.title, surface.creator]
    .filter(Boolean)
    .join(" / ");
  const exact = geoForText(exactText);
  if (exact) {
    return {
      point: exact.point,
      label: mapLabelForSurface(surface, "active"),
      inferred: exact.inferred,
    };
  }

  const folderText = surface.folders.map((folder) => folder.title).join(" / ");
  const folder = geoForText(folderText);
  if (folder) {
    return {
      point: folder.point,
      label: `${surface.folders.find((item) => item.type === "region")?.title ?? "regional context"} / inferred`,
      inferred: true,
    };
  }

  const source = geoForText(surface.sourceName);
  if (source) {
    return {
      point: source.point,
      label: `${surface.sourceName} / inferred`,
      inferred: true,
    };
  }

  return INFERRED_GLOBAL_GEO;
}

function geoForText(value: string): GeoResolution | undefined {
  for (const [pattern, point] of PLACE_COORDS) {
    if (pattern.test(value)) {
      return { point, label: value, inferred: false };
    }
  }
  return undefined;
}

function mapLabelForSurface(surface: Surface, suffix: string) {
  const place = surface.placeText || surface.folders.find((folder) => folder.type === "region")?.title;
  return `${place || surface.title} / ${suffix}`;
}

interface TileConfig {
  z: number;
  startX: number;
  startY: number;
  cols: number;
  rows: number;
}

const DETAIL_MAP: TileConfig = { z: 11, startX: 1088, startY: 710, cols: 3, rows: 2 };
const WORLD_MAP: TileConfig = { z: 2, startX: 0, startY: 1, cols: 4, rows: 2 };

function pointStyle(point: Point): CSSProperties {
  return {
    left: `${point[0]}%`,
    top: `${point[1]}%`,
  };
}

function mercatorTilePoint(geo: GeoPoint, config: TileConfig): Point {
  const n = 2 ** config.z;
  const latRad = (geo.lat * Math.PI) / 180;
  const xFloat = ((geo.lon + 180) / 360) * n;
  const yFloat =
    ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n;
  return [
    ((xFloat - config.startX) / config.cols) * 100,
    ((yFloat - config.startY) / config.rows) * 100,
  ];
}

function worldPoint(geo: GeoPoint): Point {
  return mercatorTilePoint(geo, WORLD_MAP);
}

function relationPath(a: Point, b: Point) {
  const mid = Math.max(a[0], b[0]) - 5;
  return `M ${a[0]} ${a[1]} H ${mid} V ${b[1]} H ${b[0]}`;
}

function mapPath(a: Point, b: Point) {
  const cx = (a[0] + b[0]) / 2;
  const cy = (a[1] + b[1]) / 2 - 5;
  return `M ${a[0]} ${a[1]} Q ${cx} ${cy} ${b[0]} ${b[1]}`;
}
