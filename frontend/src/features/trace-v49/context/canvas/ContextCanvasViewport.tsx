import {
  useEffect,
  useMemo,
  useRef,
  type Dispatch,
  type PointerEvent,
  type RefObject,
  type WheelEvent,
} from "react";
import type { TraceContextDataset } from "../types";
import { buildContextCanvasConnectionGeometry, visibleContextCanvasNodes } from "./connections";
import { ContextCanvasConnections } from "./ContextCanvasConnections";
import { ContextCanvasNode } from "./ContextCanvasNode";
import type { ContextCanvasAction } from "./reducer";
import type { ContextCanvasState, ContextCanvasViewportSize } from "./types";
import { panContextCanvasFromPointer, zoomContextCanvasAtPoint } from "./viewport";
import styles from "./ContextCanvas.module.css";

interface ContextCanvasViewportProps {
  readonly dataset: TraceContextDataset;
  readonly state: ContextCanvasState;
  readonly dispatch: Dispatch<ContextCanvasAction>;
  readonly containerRef: RefObject<HTMLDivElement | null>;
  readonly onViewportSizeChange: (size: ContextCanvasViewportSize) => void;
}

export function ContextCanvasViewport({
  dataset,
  state,
  dispatch,
  containerRef,
  onViewportSizeChange,
}: ContextCanvasViewportProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const composition = state.history.present;
  const nodes = useMemo(
    () => visibleContextCanvasNodes(dataset, composition),
    [dataset, composition],
  );
  const geometry = useMemo(
    () => buildContextCanvasConnectionGeometry(dataset, composition),
    [dataset, composition],
  );

  useEffect(() => {
    const element = containerRef.current;
    if (!element || typeof ResizeObserver === "undefined") return;
    const publish = () => {
      const rect = element.getBoundingClientRect();
      onViewportSizeChange({ width: rect.width, height: rect.height });
    };
    publish();
    const observer = new ResizeObserver(publish);
    observer.observe(element);
    return () => observer.disconnect();
  }, [containerRef, onViewportSizeChange]);

  function handleBackgroundPointerDown(event: PointerEvent<SVGRectElement>) {
    if (state.phase !== "READY" || event.button !== 0) return;
    event.preventDefault();
    svgRef.current?.setPointerCapture(event.pointerId);
    dispatch({
      type: "BEGIN_PAN",
      pointerId: event.pointerId,
      startClient: { x: event.clientX, y: event.clientY },
    });
  }

  function handleNodePointerDown(event: PointerEvent<SVGGElement>, nodeId: string) {
    if (state.phase !== "READY" || event.button !== 0) return;
    dispatch({
      type: "BEGIN_NODE_DRAG",
      nodeId,
      pointerId: event.pointerId,
      startClient: { x: event.clientX, y: event.clientY },
    });
  }

  function handlePointerMove(event: PointerEvent<SVGSVGElement>) {
    const interaction = state.interaction;
    if (interaction.mode === "NODE_DRAGGING" && interaction.pointerId === event.pointerId) {
      dispatch({
        type: "PREVIEW_NODE_DRAG",
        position: {
          x: interaction.originPosition.x + (event.clientX - interaction.startClient.x) / state.viewport.zoom,
          y: interaction.originPosition.y + (event.clientY - interaction.startClient.y) / state.viewport.zoom,
        },
      });
    } else if (interaction.mode === "PANNING" && interaction.pointerId === event.pointerId) {
      dispatch({
        type: "SET_VIEWPORT",
        viewport: panContextCanvasFromPointer(
          interaction.originViewport,
          interaction.startClient,
          { x: event.clientX, y: event.clientY },
        ),
      });
    }
  }

  function handlePointerEnd(event: PointerEvent<SVGSVGElement>) {
    if (state.interaction.mode === "NODE_DRAGGING" && state.interaction.pointerId === event.pointerId) {
      dispatch({ type: "END_NODE_DRAG" });
    } else if (state.interaction.mode === "PANNING" && state.interaction.pointerId === event.pointerId) {
      dispatch({ type: "END_PAN" });
    }
  }

  function handleWheel(event: WheelEvent<HTMLDivElement>) {
    event.preventDefault();
    if (state.phase === "EXPORTING" || state.interaction.mode !== "READY") return;
    const rect = event.currentTarget.getBoundingClientRect();
    const point = { x: event.clientX - rect.left, y: event.clientY - rect.top };
    const factor = Math.exp(-event.deltaY * 0.0015);
    dispatch({
      type: "SET_VIEWPORT",
      viewport: zoomContextCanvasAtPoint(state.viewport, point, state.viewport.zoom * factor),
    });
  }

  return (
    <div
      ref={containerRef}
      className={styles.viewport}
      onWheel={handleWheel}
      data-interaction={state.interaction.mode}
    >
      <svg
        id="context-canvas-workspace"
        ref={svgRef}
        className={styles.canvasSvg}
        role="application"
        tabIndex={0}
        aria-label="Context Canvas graphical workspace. Drag nodes, drag the background to pan, and use the wheel to zoom."
        aria-describedby="context-canvas-accessible-reference"
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerEnd}
        onPointerCancel={(event) => {
          const interaction = state.interaction;
          if (interaction.mode !== "READY" && interaction.pointerId === event.pointerId) {
            dispatch({ type: "CANCEL_INTERACTION" });
          }
        }}
        onKeyDown={(event) => {
          if (event.key !== "Escape") return;
          event.preventDefault();
          if (state.interaction.mode === "READY") {
            dispatch({ type: "SELECT", selection: null });
          } else {
            dispatch({ type: "CANCEL_INTERACTION" });
          }
        }}
      >
        <defs>
          <marker
            id="context-canvas-arrow"
            viewBox="0 0 8 8"
            refX="7"
            refY="4"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 8 4 L 0 8 z" className={styles.arrowMarker} />
          </marker>
        </defs>
        <rect
          className={styles.canvasBackground}
          x="0"
          y="0"
          width="100%"
          height="100%"
          onPointerDown={handleBackgroundPointerDown}
        />
        <g transform={`translate(${state.viewport.x} ${state.viewport.y}) scale(${state.viewport.zoom})`}>
          <ContextCanvasConnections
            geometry={geometry}
            selectedConnectionId={state.selection?.kind === "connection" ? state.selection.id : null}
            onSelect={(id) => dispatch({ type: "SELECT", selection: { kind: "connection", id } })}
          />
          {nodes.map((node) => (
            <ContextCanvasNode
              key={node.id}
              node={node}
              selected={state.selection?.kind === "node" && state.selection.id === node.id}
              onPointerDown={handleNodePointerDown}
              onSelect={(id) => dispatch({ type: "SELECT", selection: { kind: "node", id } })}
              onMoveBy={(entityId, delta) => dispatch({ type: "MOVE_NODE_BY", entityId, delta })}
            />
          ))}
        </g>
      </svg>
      <div className={styles.viewportReadout} aria-hidden="true">
        {Math.round(state.viewport.zoom * 100)}%
      </div>
    </div>
  );
}
