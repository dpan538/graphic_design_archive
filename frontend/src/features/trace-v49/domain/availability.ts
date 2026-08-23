export type TraceAvailability =
  | "ready"
  | "empty"
  | "not_published"
  | "held"
  | "unknown"
  | "error";

export interface TraceAvailabilityState {
  readonly state: TraceAvailability;
  readonly reasonCodes: readonly string[];
  readonly message: string;
}

export function copyAvailability(value: TraceAvailabilityState): TraceAvailabilityState {
  if (!value.state || !value.message.trim()) throw new Error("explicit TRACE availability is required");
  return Object.freeze({
    state: value.state,
    reasonCodes: Object.freeze([...value.reasonCodes].sort()),
    message: value.message,
  });
}
