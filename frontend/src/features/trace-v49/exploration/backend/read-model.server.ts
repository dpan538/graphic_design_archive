import readModelJson from "../../../../../generated/trace-exploration-v1/read-model.json" with { type: "json" };
import type { ExplorationReadModel } from "./types.ts";

const EXPECTED_FORMAT = "trace-exploration-real-read-model-v1";
const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
let validated: ExplorationReadModel | undefined;

function deepFreeze<T>(value: T): T {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const child of Object.values(value as Record<string, unknown>)) deepFreeze(child);
  }
  return value;
}

export function getExplorationReadModel(): ExplorationReadModel {
  if (validated) return validated;
  const candidate = readModelJson as unknown as ExplorationReadModel;
  if (candidate.format !== EXPECTED_FORMAT) throw new Error("Exploration read-model format mismatch");
  if (!SHA256_PATTERN.test(candidate.read_model_sha256)) throw new Error("Exploration read-model hash is invalid");
  if (candidate.source_sha !== "aca7b9627ca42776d966f96ce4bd03db1f296ae3") throw new Error("Exploration source commit mismatch");
  if (candidate.categories.length !== 4) throw new Error("Exploration four-category contract mismatch");
  if (candidate.vocabulary.some((item) => item.activation_status !== "ACTIVE_USER_VISIBLE" || !item.source_attestations?.length || !item.academic_support?.length)) {
    throw new Error("Exploration vocabulary activation contract mismatch");
  }
  if (candidate.associations.some((item) => item.active_for_proximity !== true || item.generic_association_only !== true)) {
    throw new Error("Exploration association boundary mismatch");
  }
  validated = deepFreeze(candidate);
  return validated;
}
