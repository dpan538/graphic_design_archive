import {
  boundContextCanvasHistory,
  commitContextCanvasComposition,
  contextCanvasCompositionsEqual,
  isCompositionValidForState,
  restoreContextCanvasWorkspace,
} from "./state";
import {
  CONTEXT_CANVAS_HISTORY_LIMIT,
  isFiniteCanvasPosition,
  type ContextCanvasComposition,
  type ContextCanvasEntityId,
  type ContextCanvasPosition,
  type ContextCanvasSelection,
  type ContextCanvasState,
  type ContextCanvasViewport,
} from "./types";
import { sanitizeContextCanvasViewport } from "./viewport";

export type ContextCanvasAction =
  | Readonly<{ type: "INITIALIZE"; composition?: ContextCanvasComposition; viewport?: ContextCanvasViewport }>
  | Readonly<{ type: "APPLY_TEMPLATE"; composition: ContextCanvasComposition }>
  | Readonly<{ type: "ADD_ENTITY"; entityId: ContextCanvasEntityId; position: ContextCanvasPosition }>
  | Readonly<{ type: "HIDE_ENTITY"; entityId: ContextCanvasEntityId }>
  | Readonly<{ type: "MOVE_NODE_BY"; entityId: ContextCanvasEntityId; delta: ContextCanvasPosition }>
  | Readonly<{
    type: "BEGIN_NODE_DRAG";
    nodeId: ContextCanvasEntityId;
    pointerId: number;
    startClient: ContextCanvasPosition;
  }>
  | Readonly<{ type: "PREVIEW_NODE_DRAG"; position: ContextCanvasPosition }>
  | Readonly<{ type: "END_NODE_DRAG" }>
  | Readonly<{ type: "BEGIN_PALETTE_DRAG"; entityId: ContextCanvasEntityId; pointerId: number }>
  | Readonly<{ type: "END_PALETTE_DRAG" }>
  | Readonly<{ type: "BEGIN_PAN"; pointerId: number; startClient: ContextCanvasPosition }>
  | Readonly<{ type: "END_PAN" }>
  | Readonly<{ type: "CANCEL_INTERACTION" }>
  | Readonly<{ type: "SET_VIEWPORT"; viewport: ContextCanvasViewport }>
  | Readonly<{ type: "SELECT"; selection: ContextCanvasSelection }>
  | Readonly<{ type: "UNDO" }>
  | Readonly<{ type: "REDO" }>
  | Readonly<{ type: "AUTO_ARRANGE"; positions: ContextCanvasComposition["positions"] }>
  | Readonly<{ type: "RESET_CANVAS"; composition: ContextCanvasComposition }>
  | Readonly<{ type: "EXPORT_START" }>
  | Readonly<{ type: "EXPORT_SUCCESS" }>
  | Readonly<{ type: "EXPORT_FAILURE"; message: string }>;

function freezeComposition(composition: ContextCanvasComposition): ContextCanvasComposition {
  const positions = Object.fromEntries(
    composition.visibleEntityIds.map((entityId) => [
      entityId,
      Object.freeze({ ...composition.positions[entityId] }),
    ]),
  );
  return Object.freeze({
    templateId: composition.templateId,
    templateVersion: composition.templateVersion,
    visibleEntityIds: Object.freeze([...composition.visibleEntityIds]),
    positions: Object.freeze(positions),
  });
}

function readyInteraction() {
  return Object.freeze({ mode: "READY" as const });
}

function canInteract(state: ContextCanvasState): boolean {
  return state.phase === "READY" || state.phase === "EXPORT_ERROR";
}

export function contextCanvasReducer(
  state: ContextCanvasState,
  action: ContextCanvasAction,
): ContextCanvasState {
  switch (action.type) {
    case "INITIALIZE":
      return restoreContextCanvasWorkspace(
        state,
        action.composition ?? state.history.present,
        action.viewport ?? state.viewport,
      );

    case "APPLY_TEMPLATE":
      if (!canInteract(state) || state.interaction.mode !== "READY") return state;
      return commitContextCanvasComposition(
        state,
        freezeComposition(action.composition),
        `Applied ${action.composition.templateId} template.`,
      );

    case "ADD_ENTITY": {
      if (!canInteract(state) || state.interaction.mode !== "READY") return state;
      if (!state.allowedEntityIds.includes(action.entityId) || !isFiniteCanvasPosition(action.position)) return state;
      if (state.history.present.visibleEntityIds.includes(action.entityId)) {
        return Object.freeze({
          ...state,
          selection: Object.freeze({ kind: "node", id: action.entityId }),
          interaction: readyInteraction(),
          phase: "READY",
          exportError: null,
          statusMessage: "Entity is already visible; focused the existing canvas node.",
        });
      }
      const visibleEntityIds = Object.freeze(
        [...state.history.present.visibleEntityIds, action.entityId].sort(),
      );
      const next = freezeComposition({
        ...state.history.present,
        visibleEntityIds,
        positions: { ...state.history.present.positions, [action.entityId]: action.position },
      });
      const committed = commitContextCanvasComposition(state, next, "Added entity to the canvas composition.");
      return Object.freeze({
        ...committed,
        selection: Object.freeze({ kind: "node", id: action.entityId }),
      });
    }

    case "HIDE_ENTITY": {
      if (!canInteract(state) || state.interaction.mode !== "READY") return state;
      if (action.entityId === state.rootEntityId) {
        return Object.freeze({ ...state, phase: "READY", exportError: null, statusMessage: "The selected root object cannot be removed." });
      }
      if (!state.history.present.visibleEntityIds.includes(action.entityId)) return state;
      const positions = { ...state.history.present.positions };
      delete positions[action.entityId];
      return commitContextCanvasComposition(
        state,
        freezeComposition({
          ...state.history.present,
          visibleEntityIds: state.history.present.visibleEntityIds.filter((id) => id !== action.entityId),
          positions,
        }),
        "Removed entity from the canvas composition; source data were unchanged.",
      );
    }

    case "MOVE_NODE_BY": {
      if (!canInteract(state) || state.interaction.mode !== "READY") return state;
      const origin = state.history.present.positions[action.entityId];
      if (!origin || !isFiniteCanvasPosition(action.delta)) return state;
      const nextPosition = Object.freeze({ x: origin.x + action.delta.x, y: origin.y + action.delta.y });
      const next = freezeComposition({
        ...state.history.present,
        positions: { ...state.history.present.positions, [action.entityId]: nextPosition },
      });
      const committed = commitContextCanvasComposition(state, next, "Moved canvas entity by keyboard.");
      return Object.freeze({
        ...committed,
        selection: Object.freeze({ kind: "node", id: action.entityId }),
      });
    }

    case "BEGIN_NODE_DRAG": {
      const originPosition = state.history.present.positions[action.nodeId];
      if (!canInteract(state) || state.interaction.mode !== "READY" || !originPosition) return state;
      return Object.freeze({
        ...state,
        phase: "READY",
        exportError: null,
        selection: Object.freeze({ kind: "node", id: action.nodeId }),
        interaction: Object.freeze({
          mode: "NODE_DRAGGING",
          nodeId: action.nodeId,
          pointerId: action.pointerId,
          startClient: Object.freeze({ ...action.startClient }),
          originPosition: Object.freeze({ ...originPosition }),
          baseline: freezeComposition(state.history.present),
        }),
        statusMessage: "Moving canvas entity.",
      });
    }

    case "PREVIEW_NODE_DRAG": {
      if (state.interaction.mode !== "NODE_DRAGGING" || !isFiniteCanvasPosition(action.position)) return state;
      const present = freezeComposition({
        ...state.history.present,
        positions: {
          ...state.history.present.positions,
          [state.interaction.nodeId]: action.position,
        },
      });
      return Object.freeze({
        ...state,
        history: Object.freeze({ ...state.history, present }),
      });
    }

    case "END_NODE_DRAG": {
      if (state.interaction.mode !== "NODE_DRAGGING") return state;
      const { baseline, nodeId } = state.interaction;
      if (contextCanvasCompositionsEqual(baseline, state.history.present)) {
        return Object.freeze({ ...state, interaction: readyInteraction(), statusMessage: "Canvas entity unchanged." });
      }
      return Object.freeze({
        ...state,
        history: Object.freeze({
          past: boundContextCanvasHistory([...state.history.past, baseline]),
          present: state.history.present,
          future: Object.freeze([]),
        }),
        selection: Object.freeze({ kind: "node", id: nodeId }),
        interaction: readyInteraction(),
        statusMessage: "Moved canvas entity.",
      });
    }

    case "BEGIN_PALETTE_DRAG":
      if (!canInteract(state) || state.interaction.mode !== "READY") return state;
      if (!state.allowedEntityIds.includes(action.entityId)) return state;
      return Object.freeze({
        ...state,
        phase: "READY",
        exportError: null,
        interaction: Object.freeze({
          mode: "PALETTE_DRAGGING",
          entityId: action.entityId,
          pointerId: action.pointerId,
        }),
        statusMessage: "Drag the entity onto the canvas.",
      });

    case "END_PALETTE_DRAG":
      return state.interaction.mode === "PALETTE_DRAGGING"
        ? Object.freeze({ ...state, interaction: readyInteraction(), statusMessage: "Palette drag ended without changing source data." })
        : state;

    case "BEGIN_PAN":
      if (!canInteract(state) || state.interaction.mode !== "READY") return state;
      return Object.freeze({
        ...state,
        phase: "READY",
        exportError: null,
        selection: null,
        interaction: Object.freeze({
          mode: "PANNING",
          pointerId: action.pointerId,
          startClient: Object.freeze({ ...action.startClient }),
          originViewport: state.viewport,
        }),
        statusMessage: "Panning canvas.",
      });

    case "END_PAN":
      return state.interaction.mode === "PANNING"
        ? Object.freeze({ ...state, interaction: readyInteraction(), statusMessage: "Canvas panned." })
        : state;

    case "CANCEL_INTERACTION":
      if (state.interaction.mode === "NODE_DRAGGING") {
        return Object.freeze({
          ...state,
          history: Object.freeze({ ...state.history, present: state.interaction.baseline }),
          interaction: readyInteraction(),
          statusMessage: "Node movement cancelled.",
        });
      }
      return Object.freeze({ ...state, interaction: readyInteraction(), statusMessage: "Interaction cancelled." });

    case "SET_VIEWPORT":
      if (state.phase === "EXPORTING") return state;
      return Object.freeze({
        ...state,
        phase: state.phase === "INITIALIZING" ? "INITIALIZING" : "READY",
        exportError: null,
        viewport: sanitizeContextCanvasViewport(action.viewport),
      });

    case "SELECT":
      if (!canInteract(state) || state.interaction.mode !== "READY") return state;
      return Object.freeze({ ...state, phase: "READY", exportError: null, selection: action.selection, statusMessage: action.selection ? "Canvas item selected." : "Canvas selection cleared." });

    case "UNDO": {
      if (!canInteract(state) || state.interaction.mode !== "READY" || state.history.past.length === 0) return state;
      const present = state.history.past[state.history.past.length - 1];
      return Object.freeze({
        ...state,
        history: Object.freeze({
          past: Object.freeze(state.history.past.slice(0, -1)),
          present,
          future: Object.freeze(
            [state.history.present, ...state.history.future].slice(0, CONTEXT_CANVAS_HISTORY_LIMIT),
          ),
        }),
        selection: null,
        phase: "READY",
        exportError: null,
        statusMessage: "Undid the last composition change.",
      });
    }

    case "REDO": {
      if (!canInteract(state) || state.interaction.mode !== "READY" || state.history.future.length === 0) return state;
      const [present, ...future] = state.history.future;
      return Object.freeze({
        ...state,
        history: Object.freeze({
          past: boundContextCanvasHistory([...state.history.past, state.history.present]),
          present,
          future: Object.freeze(future),
        }),
        selection: null,
        phase: "READY",
        exportError: null,
        statusMessage: "Redid the composition change.",
      });
    }

    case "AUTO_ARRANGE":
      if (!canInteract(state) || state.interaction.mode !== "READY") return state;
      return commitContextCanvasComposition(
        state,
        freezeComposition({ ...state.history.present, positions: action.positions }),
        "Auto-arranged visible entities with the deterministic lane layout.",
      );

    case "RESET_CANVAS":
      if (!canInteract(state)) return state;
      if (!isCompositionValidForState(state, action.composition)) return state;
      return Object.freeze({
        ...state,
        history: Object.freeze({
          past: Object.freeze([]),
          present: freezeComposition(action.composition),
          future: Object.freeze([]),
        }),
        selection: null,
        interaction: readyInteraction(),
        phase: "READY",
        exportError: null,
        statusMessage: "Reset the current template and cleared local composition history.",
      });

    case "EXPORT_START":
      if (state.phase === "INITIALIZING" || state.phase === "EXPORTING" || state.interaction.mode !== "READY") return state;
      return Object.freeze({ ...state, phase: "EXPORTING", exportError: null, interaction: readyInteraction(), statusMessage: "Preparing PNG export." });

    case "EXPORT_SUCCESS":
      return Object.freeze({ ...state, phase: "READY", exportError: null, statusMessage: "PNG export ready and downloaded." });

    case "EXPORT_FAILURE":
      return Object.freeze({ ...state, phase: "EXPORT_ERROR", exportError: action.message, statusMessage: "PNG export failed." });
  }
}
