import "server-only";

import { createHash } from "node:crypto";
import { closeSync, existsSync, openSync, readFileSync, readSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import {
  projectRealContextValidationDataset,
  TRACE_CONTEXT_REALDATA_FROZEN_INPUT_SHA256,
} from "./project.server";
import type {
  TraceContextValidationFolderCandidate,
  TraceContextValidationFolderType,
  TraceContextValidationLookup,
  TraceContextValidationRecordCandidate,
  TraceContextValidationSampleOption,
} from "./types";

export const TRACE_CONTEXT_REALDATA_ENV_GATE = "CONTEXT_CANVAS_REAL_VALIDATION" as const;
export const TRACE_CONTEXT_EXPECTED_CANONICAL_COUNT = 15_923;
export const TRACE_CONTEXT_EXPECTED_PUBLIC_COUNT = 7_995;
export const TRACE_CONTEXT_EXPECTED_HELD_COUNT = 7_928;
export const TRACE_CONTEXT_EXPECTED_PUBLIC_FOLDER_MEMBERSHIP_COUNT = 24_102;
export const TRACE_CONTEXT_EXPECTED_PUBLIC_CONTROLLED_ASSIGNMENT_COUNT = 16_106;

const EXPECTED_FOLDER_COUNTS = Object.freeze({
  medium: 7_995,
  theme: 7_996,
  movement: 115,
  region: 7_996,
});
const VALID_FOLDER_TYPES = new Set<TraceContextValidationFolderType>([
  "medium",
  "theme",
  "movement",
  "region",
]);
const PUBLIC_STABLE_ID_PATTERN = /^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u;
const NOT_AVAILABLE_FAILURE = Object.freeze({
  status: "error" as const,
  code: "RECORD_NOT_AVAILABLE" as const,
  message: "The requested record is not available in this validation workspace.",
});

export interface TraceContextValidationSourceIndex {
  readonly canonicalCount: number;
  readonly publicCount: number;
  readonly heldCount: number;
  readonly publicFolderMembershipCount: number;
  readonly publicControlledAssignmentCount: number;
  readonly eligibleStableIds: readonly string[];
  readonly heldStableIds: ReadonlySet<string>;
  readonly candidates: readonly TraceContextValidationRecordCandidate[];
  readonly candidateByStableId: ReadonlyMap<string, TraceContextValidationRecordCandidate>;
}

let cachedIndex: TraceContextValidationSourceIndex | null = null;

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function chunks<T>(values: readonly T[], size: number): readonly (readonly T[])[] {
  const result: T[][] = [];
  for (let start = 0; start < values.length; start += size) {
    result.push(values.slice(start, start + size));
  }
  return result;
}

function locateRepositoryRoot(): string {
  for (const candidate of [process.cwd(), resolve(process.cwd(), "..")]) {
    if (
      existsSync(resolve(candidate, "database/FREEZE_V49.json"))
      && existsSync(resolve(candidate, "data/prefreeze_candidate_v48.sqlite"))
    ) return candidate;
  }
  throw new Error("unable to locate the frozen v49 repository inputs");
}

function sha256File(path: string): string {
  const descriptor = openSync(path, "r");
  const hash = createHash("sha256");
  const buffer = Buffer.allocUnsafe(1024 * 1024);
  try {
    let bytesRead = 0;
    do {
      bytesRead = readSync(descriptor, buffer, 0, buffer.length, null);
      if (bytesRead > 0) hash.update(buffer.subarray(0, bytesRead));
    } while (bytesRead > 0);
  } finally {
    closeSync(descriptor);
  }
  return hash.digest("hex");
}

function verifyFrozenInputs(root: string): void {
  for (const [relativePath, expectedSha256] of Object.entries(
    TRACE_CONTEXT_REALDATA_FROZEN_INPUT_SHA256,
  )) {
    const actualSha256 = sha256File(resolve(root, relativePath));
    if (actualSha256 !== expectedSha256) {
      throw new Error(`frozen v49 validation input checksum differs: ${relativePath}`);
    }
  }
}

function parseEligibilityLedger(path: string): {
  readonly eligible: Set<string>;
  readonly held: Set<string>;
} {
  const lines = readFileSync(path, "utf8").split(/\r?\n/u).filter(Boolean);
  const headers = lines.shift()?.split("\t") ?? [];
  const stableIdIndex = headers.indexOf("surface_id_exact");
  const dispositionIndex = headers.indexOf("research_disposition");
  if (stableIdIndex < 0 || dispositionIndex < 0) {
    throw new Error("v49 eligibility ledger columns are missing");
  }

  const eligible = new Set<string>();
  const held = new Set<string>();
  for (const line of lines) {
    const cells = line.split("\t");
    const stableId = cells[stableIdIndex] ?? "";
    const disposition = cells[dispositionIndex] ?? "";
    if (!PUBLIC_STABLE_ID_PATTERN.test(stableId)) {
      throw new Error("v49 eligibility ledger contains an invalid stable ID");
    }
    if (eligible.has(stableId) || held.has(stableId)) {
      throw new Error(`duplicate v49 eligibility identity: ${stableId}`);
    }
    if (disposition === "eligible") eligible.add(stableId);
    else if (disposition === "held") held.add(stableId);
    else throw new Error(`unclassified v49 eligibility identity: ${stableId}`);
  }
  if (
    eligible.size !== TRACE_CONTEXT_EXPECTED_PUBLIC_COUNT
    || held.size !== TRACE_CONTEXT_EXPECTED_HELD_COUNT
    || eligible.size + held.size !== TRACE_CONTEXT_EXPECTED_CANONICAL_COUNT
  ) throw new Error("v49 eligibility counts do not reconcile");
  return { eligible, held };
}

function readFrozenIndex(): TraceContextValidationSourceIndex {
  const root = locateRepositoryRoot();
  verifyFrozenInputs(root);
  const freeze = JSON.parse(readFileSync(resolve(root, "database/FREEZE_V49.json"), "utf8")) as {
    objectCount?: number;
    eligibleCount?: number;
    heldCount?: number;
    relationshipCount?: number;
    acceptedTraceCount?: number;
  };
  if (
    freeze.objectCount !== TRACE_CONTEXT_EXPECTED_CANONICAL_COUNT
    || freeze.eligibleCount !== TRACE_CONTEXT_EXPECTED_PUBLIC_COUNT
    || freeze.heldCount !== TRACE_CONTEXT_EXPECTED_HELD_COUNT
    || freeze.relationshipCount !== 47_982
    || freeze.acceptedTraceCount !== 0
  ) throw new Error("frozen v49 release counts differ from the validation contract");

  const { eligible, held } = parseEligibilityLedger(resolve(
    root,
    "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv",
  ));
  const foldersByStableId = new Map<string, TraceContextValidationFolderCandidate[]>();
  const titlesByStableId = new Map<string, string>();
  const folderCounts = new Map<TraceContextValidationFolderType, number>();
  const eligibleStableIds = [...eligible].sort(compareText);
  let publicFolderMembershipCount = 0;

  const sqlitePath = resolve(root, "data/prefreeze_candidate_v48.sqlite");
  const { DatabaseSync } = createRequire(import.meta.url)("node:sqlite") as typeof import("node:sqlite");
  const database = new DatabaseSync(`file:${sqlitePath}?mode=ro&immutable=1`, {
    readOnly: true,
  });
  try {
    database.exec("PRAGMA query_only=ON");
    const objectCount = Number(database.prepare("SELECT count(*) AS count FROM objects").get()?.count);
    const folderCount = Number(database.prepare("SELECT count(*) AS count FROM object_folder_refs").get()?.count);
    if (objectCount !== TRACE_CONTEXT_EXPECTED_CANONICAL_COUNT || folderCount !== 47_982) {
      throw new Error("frozen SQLite reconciliation counts differ from the v49 freeze");
    }

    for (const stableIdChunk of chunks(eligibleStableIds, 400)) {
      const placeholders = stableIdChunk.map(() => "?").join(",");
      const statement = database.prepare(
        `SELECT surface_id, title FROM objects WHERE surface_id IN (${placeholders}) ORDER BY surface_id`,
      );
      for (const row of statement.iterate(...stableIdChunk) as Iterable<{
        surface_id: string;
        title: string;
      }>) {
        if (titlesByStableId.has(row.surface_id)) {
          throw new Error(`duplicate public validation object: ${row.surface_id}`);
        }
        titlesByStableId.set(row.surface_id, row.title);
        foldersByStableId.set(row.surface_id, []);
      }
    }

    for (const stableIdChunk of chunks(eligibleStableIds, 400)) {
      const placeholders = stableIdChunk.map(() => "?").join(",");
      const statement = database.prepare(
        `SELECT surface_id, folder_id, folder_type, title FROM object_folder_refs WHERE surface_id IN (${placeholders}) ORDER BY surface_id, folder_type, folder_id`,
      );
      for (const row of statement.iterate(...stableIdChunk) as Iterable<{
        surface_id: string;
        folder_id: string;
        folder_type: string;
        title: string;
      }>) {
        if (!VALID_FOLDER_TYPES.has(row.folder_type as TraceContextValidationFolderType)) {
          throw new Error(`unmapped Context folder type: ${row.folder_type}`);
        }
        const folderType = row.folder_type as TraceContextValidationFolderType;
        const target = foldersByStableId.get(row.surface_id);
        if (!target) throw new Error(`dangling public Context folder row: ${row.surface_id}`);
        target.push(Object.freeze({
          folderToken: row.folder_id,
          folderType,
          label: row.title,
        }));
        publicFolderMembershipCount += 1;
        folderCounts.set(folderType, (folderCounts.get(folderType) ?? 0) + 1);
      }
    }
  } finally {
    database.close();
  }

  if (titlesByStableId.size !== TRACE_CONTEXT_EXPECTED_PUBLIC_COUNT) {
    throw new Error("public v49 object titles do not reconcile with eligibility");
  }
  if (publicFolderMembershipCount !== TRACE_CONTEXT_EXPECTED_PUBLIC_FOLDER_MEMBERSHIP_COUNT) {
    throw new Error("public v49 folder memberships do not reconcile");
  }
  for (const [folderType, expected] of Object.entries(EXPECTED_FOLDER_COUNTS)) {
    if (folderCounts.get(folderType as TraceContextValidationFolderType) !== expected) {
      throw new Error(`public v49 ${folderType} count does not reconcile`);
    }
  }

  const frozenEligibleStableIds = Object.freeze(eligibleStableIds);
  const candidates = Object.freeze(frozenEligibleStableIds.map((stableId) => {
    const title = titlesByStableId.get(stableId);
    const folders = foldersByStableId.get(stableId);
    if (title === undefined || folders === undefined || folders.length === 0) {
      throw new Error(`public Context candidate is incomplete: ${stableId}`);
    }
    return Object.freeze({
      stableId,
      title,
      folders: Object.freeze([...folders]),
    });
  }));
  const candidateByStableId = new Map(candidates.map((candidate) => [candidate.stableId, candidate]));
  const publicControlledAssignmentCount = candidates.reduce(
    (count, candidate) => count + candidate.folders.filter(
      (folder) => folder.folderType !== "region",
    ).length,
    0,
  );
  if (publicControlledAssignmentCount !== TRACE_CONTEXT_EXPECTED_PUBLIC_CONTROLLED_ASSIGNMENT_COUNT) {
    throw new Error("public v49 controlled assignment candidates do not reconcile");
  }

  return Object.freeze({
    canonicalCount: TRACE_CONTEXT_EXPECTED_CANONICAL_COUNT,
    publicCount: frozenEligibleStableIds.length,
    heldCount: held.size,
    publicFolderMembershipCount,
    publicControlledAssignmentCount,
    eligibleStableIds: frozenEligibleStableIds,
    heldStableIds: held,
    candidates,
    candidateByStableId,
  });
}

export function resetRealContextValidationSourceIndexForTests(): void {
  cachedIndex = null;
}

export function loadRealContextValidationSourceIndexForVerification(
  bypassCache = false,
): TraceContextValidationSourceIndex {
  if (!bypassCache && cachedIndex) return cachedIndex;
  const index = readFrozenIndex();
  if (!bypassCache) cachedIndex = index;
  return index;
}

export function realContextValidationEnabled(): boolean {
  return process.env[TRACE_CONTEXT_REALDATA_ENV_GATE] === "1";
}

export function lookupRealContextValidationDataset(
  requestedRecordId: string | undefined,
  options: Readonly<{ allowWithoutGate?: boolean }> = {},
): TraceContextValidationLookup {
  if (requestedRecordId !== undefined && !PUBLIC_STABLE_ID_PATTERN.test(requestedRecordId)) {
    return Object.freeze({
      status: "error" as const,
      code: "INVALID_RECORD_ID" as const,
      message: "The record parameter is not a valid public stable ID.",
    });
  }
  if (!options.allowWithoutGate && !realContextValidationEnabled()) {
    return Object.freeze({
      status: "error" as const,
      code: "VALIDATION_DATA_NOT_GENERATED" as const,
      message: "Real v49 Context validation is disabled. Set the local validation gate to enable it.",
    });
  }

  let index: TraceContextValidationSourceIndex;
  try {
    index = loadRealContextValidationSourceIndexForVerification();
  } catch {
    return Object.freeze({
      status: "error" as const,
      code: "DATA_INTEGRITY_ERROR" as const,
      message: "The local validation sources failed integrity reconciliation.",
    });
  }
  const stableId = requestedRecordId ?? index.eligibleStableIds[0];
  const candidate = stableId ? index.candidateByStableId.get(stableId) : undefined;
  if (!candidate) return NOT_AVAILABLE_FAILURE;

  try {
    return Object.freeze({
      status: "ready" as const,
      projection: projectRealContextValidationDataset(candidate),
    });
  } catch {
    return Object.freeze({
      status: "error" as const,
      code: "VALIDATION_PROJECTION_ERROR" as const,
      message: "The selected validation record could not be projected safely.",
    });
  }
}

export function getRealContextValidationSampleOptions(
  limit = 5,
): readonly TraceContextValidationSampleOption[] {
  if (!realContextValidationEnabled()) return Object.freeze([]);
  const index = loadRealContextValidationSourceIndexForVerification();
  const safeLimit = Math.max(1, Math.min(8, Math.trunc(limit)));
  const selected = new Set<number>();
  for (let offset = 0; offset < safeLimit; offset += 1) {
    selected.add(Math.round((index.candidates.length - 1) * (offset / Math.max(1, safeLimit - 1))));
  }
  return Object.freeze([...selected].sort((left, right) => left - right).map((position) => {
    const candidate = index.candidates[position];
    return Object.freeze({ stableId: candidate.stableId, title: candidate.title });
  }));
}
