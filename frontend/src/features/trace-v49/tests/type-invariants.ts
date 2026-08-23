import type {
  TraceCuratedMembership,
  TraceSemanticEdge,
  TraceVisualGuide,
} from "../index";

function acceptsSemanticEdge(_edge: TraceSemanticEdge): void {}

declare const membership: TraceCuratedMembership;
declare const guide: TraceVisualGuide;

// Compile-time proof that memberships and renderer guides cannot be promoted.
// @ts-expect-error TRACE-INV-003: membership is not a semantic relation.
acceptsSemanticEdge(membership);
// @ts-expect-error TRACE-INV-005: a visual guide is not a semantic edge.
acceptsSemanticEdge(guide);
