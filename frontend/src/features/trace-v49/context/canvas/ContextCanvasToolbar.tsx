import type { ChangeEvent } from "react";
import { CONTEXT_CANVAS_TEMPLATES } from "./templates";
import type { ContextCanvasTemplateId } from "./types";
import styles from "./ContextCanvas.module.css";

interface ContextCanvasToolbarProps {
  readonly templateId: ContextCanvasTemplateId;
  readonly canUndo: boolean;
  readonly canRedo: boolean;
  readonly canZoomIn: boolean;
  readonly canZoomOut: boolean;
  readonly exporting: boolean;
  readonly interactionLocked: boolean;
  readonly onTemplateChange: (templateId: ContextCanvasTemplateId) => void;
  readonly onUndo: () => void;
  readonly onRedo: () => void;
  readonly onAutoArrange: () => void;
  readonly onFit: () => void;
  readonly onZoomIn: () => void;
  readonly onZoomOut: () => void;
  readonly onResetView: () => void;
  readonly onResetCanvas: () => void;
  readonly onExportPng: () => void;
}

export function ContextCanvasToolbar({
  templateId,
  canUndo,
  canRedo,
  canZoomIn,
  canZoomOut,
  exporting,
  interactionLocked,
  onTemplateChange,
  onUndo,
  onRedo,
  onAutoArrange,
  onFit,
  onZoomIn,
  onZoomOut,
  onResetView,
  onResetCanvas,
  onExportPng,
}: ContextCanvasToolbarProps) {
  function handleTemplateChange(event: ChangeEvent<HTMLSelectElement>) {
    onTemplateChange(event.target.value as ContextCanvasTemplateId);
  }

  return (
    <div className={styles.toolbar} role="toolbar" aria-label="Context Canvas controls">
      <label className={styles.templateControl}>
        <span>Template</span>
        <select
          value={templateId}
          disabled={interactionLocked}
          aria-label="Context Canvas template"
          onChange={handleTemplateChange}
        >
          {CONTEXT_CANVAS_TEMPLATES.map((template) => (
            <option key={template.templateId} value={template.templateId}>{template.label}</option>
          ))}
        </select>
      </label>
      <div className={styles.toolbarGroup} aria-label="Composition history">
        <button type="button" onClick={onUndo} disabled={!canUndo || interactionLocked} aria-label="Undo composition change">Undo</button>
        <button type="button" onClick={onRedo} disabled={!canRedo || interactionLocked} aria-label="Redo composition change">Redo</button>
      </div>
      <div className={styles.toolbarGroup} aria-label="Canvas layout">
        <button type="button" onClick={onAutoArrange} disabled={interactionLocked}>Auto Arrange</button>
        <button type="button" onClick={onFit} disabled={interactionLocked}>Fit</button>
      </div>
      <div className={styles.toolbarGroup} aria-label="Canvas zoom">
        <button type="button" onClick={onZoomOut} disabled={interactionLocked || !canZoomOut} aria-label="Zoom out">Zoom −</button>
        <button type="button" onClick={onZoomIn} disabled={interactionLocked || !canZoomIn} aria-label="Zoom in">Zoom +</button>
        <button type="button" onClick={onResetView} disabled={interactionLocked}>Reset View</button>
      </div>
      <div className={styles.toolbarGroup} aria-label="Canvas reset and export">
        <button type="button" onClick={onResetCanvas} disabled={interactionLocked}>Reset Canvas</button>
        <button
          type="button"
          className={styles.exportButton}
          onClick={onExportPng}
          disabled={interactionLocked || exporting}
          aria-busy={exporting}
        >
          {exporting ? "Exporting PNG…" : "Export PNG"}
        </button>
      </div>
    </div>
  );
}
