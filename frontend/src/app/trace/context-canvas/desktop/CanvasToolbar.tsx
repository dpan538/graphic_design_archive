import {
  ARRANGE,
  EXPORT_PNG,
  EXPORTING,
  FIT,
  REDO,
  RESET_CANVAS,
  RESET_CANVAS_LABEL,
  UNDO,
  ZOOM_IN,
  ZOOM_OUT,
} from "../lib/content";
import styles from "./CanvasToolbar.module.css";

/* 03 · 07 — the canvas toolbar (§7g): one compact line under the
   stage, subordinate to it — the existing actions only (zoom, fit,
   arrange · undo, redo, reset · export), as small text controls, the
   export the one outlined; and the status line, read aloud, beside it.
   No new behaviour. */

export interface CanvasToolbarActions {
  readonly zoomIn: () => void;
  readonly zoomOut: () => void;
  readonly fit: () => void;
  readonly arrange: () => void;
  readonly undo: () => void;
  readonly redo: () => void;
  readonly resetCanvas: () => void;
  readonly exportPng: () => void;
}

export interface CanvasToolbarProps {
  readonly zoom: number;
  readonly canUndo: boolean;
  readonly canRedo: boolean;
  readonly canZoomIn: boolean;
  readonly canZoomOut: boolean;
  readonly exporting: boolean;
  readonly locked: boolean;
  readonly status: string;
  readonly exportError: string | null;
  readonly actions: CanvasToolbarActions;
}

export default function CanvasToolbar({
  zoom,
  canUndo,
  canRedo,
  canZoomIn,
  canZoomOut,
  exporting,
  locked,
  status,
  exportError,
  actions,
}: CanvasToolbarProps) {
  return (
    <div className={styles.bar}>
      <div className={styles.tools} role="toolbar" aria-label="Canvas tools">
        <button type="button" onClick={actions.zoomOut} disabled={locked || !canZoomOut} aria-label={ZOOM_OUT}>−</button>
        <span className={`${styles.zoom} tnum`} aria-hidden="true">{Math.round(zoom * 100)}%</span>
        <button type="button" onClick={actions.zoomIn} disabled={locked || !canZoomIn} aria-label={ZOOM_IN}>+</button>
        <span className={styles.rule} aria-hidden="true" />
        <button type="button" onClick={actions.fit} disabled={locked}>{FIT}</button>
        <button type="button" onClick={actions.arrange} disabled={locked}>{ARRANGE}</button>
        <span className={styles.rule} aria-hidden="true" />
        <button type="button" onClick={actions.undo} disabled={locked || !canUndo}>{UNDO}</button>
        <button type="button" onClick={actions.redo} disabled={locked || !canRedo}>{REDO}</button>
        <button type="button" onClick={actions.resetCanvas} disabled={locked} aria-label={RESET_CANVAS_LABEL}>{RESET_CANVAS}</button>
        <span className={styles.rule} aria-hidden="true" />
        <button
          type="button"
          className={styles.export}
          onClick={actions.exportPng}
          disabled={locked || exporting}
          aria-busy={exporting || undefined}
        >
          {exporting ? EXPORTING : EXPORT_PNG}
        </button>
      </div>
      <p className={styles.status}>
        <span role="status" aria-live="polite" aria-atomic="true">{status}</span>
        {exportError ? <span role="alert" className={styles.alert}>{exportError}</span> : null}
      </p>
    </div>
  );
}
