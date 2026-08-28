import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const REQUIRED_SOURCE_SHA = "3d7536b4588032d806b6492a1be97b59891ca031";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const REPOSITORY_ROOT = resolve(SCRIPT_DIR, "../..");

const LEGACY_EXECUTION_DIRS = [
  "scripts/exploration-v49-analysis",
  "scripts/exploration-v49-similarity",
  "scripts/exploration-v49-nlp",
];

const SEALED_EVIDENCE_DIRS = [
  "docs/research/trace-v49-exploration-similarity-round1",
  "docs/audits/v49-exploration-similarity-round1",
  "docs/research/trace-v49-exploration-nlp-round1",
  "docs/audits/v49-exploration-nlp-round1",
];

const MEASUREMENT_ONLY_METRICS = new Set([
  "implementationFileCount",
  "databaseFilesChanged",
  "databaseVersion",
  "databaseUnmanifestedAdditiveFileCount",
]);

const EXTERNAL_MODEL_DEPENDENCIES = new Set([
  "transformers",
  "sentence-transformers",
  "sentence_transformers",
  "huggingface_hub",
  "flagembedding",
  "fasttext",
  "faiss",
  "faiss-cpu",
  "hnswlib",
]);

const VECTOR_DATABASE_DEPENDENCIES = new Set([
  "chromadb",
  "lancedb",
  "milvus",
  "pgvector",
  "pinecone",
  "qdrant-client",
  "weaviate-client",
]);

const CANDIDATE_PATTERNS = [
  ["ARCHIVE_OBJECT_FIELD", /\b(?:archiveObjectId|objectId|recordId|surfaceId|sourceObjectId|objectTitle|thumbnailUrl|recordUrl|objectHref)\b/i],
  ["SEARCH_RECORD_DTO_IMPORT", /(?:import|require)[^\n]*(?:search-v49|archive-data|read-platform)/i],
  ["CONTEXT_IMPORT", /(?:import|require)[^\n]*(?:trace-v49\/context|\/context\/)/i],
  ["SPACETIME_IMPORT", /(?:import|require)[^\n]*(?:trace-v49\/spacetime|\/spacetime\/)/i],
  ["EXTERNAL_MODEL_REFERENCE", /\b(?:Qwen|multilingual-e5|BGE-M3|Jina embeddings|fastText LID|SentenceTransformers|FlagEmbedding)\b/i],
  ["EXTERNAL_MODEL_IMPORT", /(?:import|require|from)[^\n]*(?:transformers|sentence_transformers|huggingface_hub|FlagEmbedding|fasttext|faiss|hnswlib)/i],
  ["MODEL_DOWNLOAD_TARGET", /(?:snapshot_download|from_pretrained|hf_hub_download|model[_-]?download)/i],
  ["NEAREST_NEIGHBOR", /\bnearest[_-]?neighbors?\b/i],
  ["OBJECT_SIMILARITY", /\b(?:object[_-]?similarity|object[_-]?affinity|object[_-]?pair[_-]?(?:score|rank))\b/i],
  ["SIMILARITY_CLUSTER", /\bsimilarity cluster\b/i],
  ["OBJECT_CARD", /\b(?:ObjectCard|objectCardDto|related objects|related records|similar works)\b/i],
  ["RECORD_ROUTE", /(?:\/surfaces\/|objectDetailRoute|recordDetailRoute)/i],
  ["VECTOR_DATABASE", /\b(?:vector database|vector db|chromadb|lancedb|milvus|pgvector|pinecone|qdrant|weaviate)\b/i],
];

function stripDenialDeclarations(source) {
  return source.replace(
    /\/\* exploration-guard:allow-denial-start \*\/[\s\S]*?\/\* exploration-guard:allow-denial-end \*\//g,
    "",
  );
}

export function scanCandidateSource(source, path = "candidate") {
  const scanned = stripDenialDeclarations(source);
  return CANDIDATE_PATTERNS.flatMap(([ruleId, pattern]) => {
    const match = scanned.match(pattern);
    return match ? [{ path, ruleId, match: match[0].replace(/\s+/g, " ").slice(0, 160) }] : [];
  });
}

function walkFiles(root) {
  if (!existsSync(root)) return [];
  const files = [];
  const visit = (path) => {
    const stat = statSync(path);
    if (stat.isDirectory()) {
      for (const entry of readdirSync(path).sort()) visit(join(path, entry));
    } else if (stat.isFile()) {
      files.push(path);
    }
  };
  visit(root);
  return files;
}

function gitChangedFiles(pathspec) {
  const args = ["diff", "--name-only", REQUIRED_SOURCE_SHA, "--", ...pathspec];
  const output = execFileSync("git", args, {
    cwd: REPOSITORY_ROOT,
    encoding: "utf8",
  }).trim();
  return output === "" ? [] : output.split("\n").filter(Boolean);
}

function dependencyDecision(packageJson) {
  const dependencies = {
    ...(packageJson.dependencies ?? {}),
    ...(packageJson.devDependencies ?? {}),
    ...(packageJson.optionalDependencies ?? {}),
  };
  const names = Object.keys(dependencies).map((name) => name.toLowerCase());
  return {
    external: names.filter((name) => EXTERNAL_MODEL_DEPENDENCIES.has(name)),
    vector: names.filter((name) => VECTOR_DATABASE_DEPENDENCIES.has(name)),
  };
}

function collectImplementationFiles() {
  const roots = [
    join(REPOSITORY_ROOT, "frontend/src/lib/trace"),
    join(REPOSITORY_ROOT, "frontend/src/features/trace-v49/exploration"),
  ];
  return roots.flatMap(walkFiles).filter((path) => /\.(?:ts|tsx|js|mjs|cjs)$/.test(path));
}

export function evaluateGovernedDatabaseFreezeReceipt(receipt, launchFailure = "") {
  const failures = [];
  if (launchFailure) failures.push(`governed database freeze verification failed: ${launchFailure}`);
  if (!receipt) {
    if (!launchFailure) failures.push("governed database freeze verifier returned no receipt");
    return { receipt: null, failures };
  }
  if (receipt.status !== "PASS") failures.push(`database freeze status is ${receipt.status}`);
  if (receipt.frozenPathDriftCount !== 0) {
    failures.push(`database frozen-path drift count is ${receipt.frozenPathDriftCount}`);
  }
  return { receipt, failures };
}

function auditGovernedDatabaseFreeze() {
  const verifier = join(REPOSITORY_ROOT, "scripts/repository/verify_v49_database_freeze.py");
  try {
    const output = execFileSync(
      "python3",
      ["-B", verifier, "--repo", REPOSITORY_ROOT],
      { cwd: REPOSITORY_ROOT, encoding: "utf8" },
    ).trim();
    const receipt = JSON.parse(output);
    return evaluateGovernedDatabaseFreezeReceipt(receipt);
  } catch (error) {
    const stderr = typeof error?.stderr === "string" ? error.stderr.trim() : "";
    const message = stderr || error?.message || "unknown verifier failure";
    return evaluateGovernedDatabaseFreezeReceipt(null, message);
  }
}

function auditPolicyDocuments() {
  const projectLogPath = join(REPOSITORY_ROOT, "PROJECT_LOG.md");
  const pointerPath = join(REPOSITORY_ROOT, "docs/research/EXPLORATION_CURRENT.md");
  const registryPath = join(
    REPOSITORY_ROOT,
    "docs/research/trace-v49-exploration-conceptual-reset/02_BAD_PRACTICE_REGISTRY.tsv",
  );
  const failures = [];
  if (!existsSync(pointerPath)) failures.push("current Exploration pointer is missing");
  if (!existsSync(registryPath)) failures.push("bad-practice registry is missing");
  const projectLog = readFileSync(projectLogPath, "utf8");
  for (const required of [
    "EXPLORATION_FIELD=CONCEPTUAL_RELATION_INSPIRATION_FIELD",
    "EXPLORATION_OBJECT_CENTRIC_BRANCH=SUPERSEDED",
    "EXPLORATION_OBJECT_NLP_BRANCH=SUPERSEDED",
    "EXPLORATION_PRIMARY_UNIT=CONCEPTUAL_RELATION_NODE",
    "EXPLORATION_FRONTEND_OBJECT_EXPOSURE=ZERO",
    "EXPLORATION_EXTERNAL_MODEL_POLICY=DENY_BY_DEFAULT",
    "EXPLORATION_APPROVED_EXTERNAL_MODEL_COUNT=0",
    "EXPLORATION_RELATION_VOCABULARY=RESEARCH_NEXT",
    "EXPLORATION_RENDERER=NOT_IMPLEMENTED",
    "EXPLORATION_PUBLIC_ROUTE=NOT_IMPLEMENTED",
  ]) {
    if (!projectLog.includes(required)) failures.push(`PROJECT_LOG missing ${required}`);
  }
  for (const obsolete of [
    "EXPLORATION_FIELD=OPEN_ENDED_DATA_MINING",
    "EXPLORATION_CANDIDATE_RETRIEVAL=CG-CUR-4_SELECTED",
    "EXPLORATION_HUMAN_REVIEW=NEXT",
  ]) {
    if (projectLog.includes(obsolete)) failures.push(`PROJECT_LOG retains ${obsolete}`);
  }
  let badPracticeRuleCount = 0;
  if (existsSync(registryPath)) {
    const rows = readFileSync(registryPath, "utf8").trim().split("\n").slice(1);
    badPracticeRuleCount = rows.length;
    if (badPracticeRuleCount !== 30) failures.push(`bad-practice rule count is ${badPracticeRuleCount}`);
    if (rows.some((row) => !row.endsWith("\tACTIVE"))) {
      failures.push("bad-practice registry contains a non-ACTIVE rule");
    }
  }
  return { failures, badPracticeRuleCount };
}

function countRule(rows, ruleId) {
  return rows.filter((row) => row.ruleId === ruleId).length;
}

export function auditActiveRepository() {
  const implementationFiles = collectImplementationFiles();
  const activeRows = implementationFiles.flatMap((path) =>
    scanCandidateSource(readFileSync(path, "utf8"), relative(REPOSITORY_ROOT, path)),
  );
  const packageJson = JSON.parse(
    readFileSync(join(REPOSITORY_ROOT, "frontend/package.json"), "utf8"),
  );
  const dependencies = dependencyDecision(packageJson);
  const policyDocuments = auditPolicyDocuments();
  const legacyExecutionDirsRemaining = LEGACY_EXECUTION_DIRS.filter((path) =>
    existsSync(join(REPOSITORY_ROOT, path)),
  );
  const oldPackageScripts = Object.entries(packageJson.scripts ?? {})
    .filter(([, command]) => /exploration-v49-(?:analysis|similarity|nlp)|generate:exploration-v49-round1|verify:exploration-v49-round1|benchmark:exploration-v49-round1/.test(command))
    .map(([name]) => name);
  const publicRoutePaths = [
    "frontend/src/app/trace/exploration",
    "frontend/src/app/api/trace/exploration",
    "frontend/src/app/api/v1/trace/exploration",
  ].filter((path) => existsSync(join(REPOSITORY_ROOT, path)));
  const sealedEvidenceChanges = gitChangedFiles(SEALED_EVIDENCE_DIRS);
  const searchChanges = gitChangedFiles([
    "frontend/src/app/search",
    "frontend/src/components/archive/shell/search.tsx",
    "frontend/src/features/search-v49",
    "frontend/scripts/generate-search-v49.mjs",
    "frontend/scripts/test-search-v49.mjs",
  ]);
  const contextChanges = gitChangedFiles(["frontend/src/features/trace-v49/context"]);
  const spacetimeChanges = gitChangedFiles(["frontend/src/features/trace-v49/spacetime"]);
  const databaseChanges = gitChangedFiles(["database"]);
  const databaseFreeze = auditGovernedDatabaseFreeze();

  const metrics = {
    implementationFileCount: implementationFiles.length,
    activeExplorationArchiveObjectFieldCount: countRule(activeRows, "ARCHIVE_OBJECT_FIELD"),
    activeExplorationRecordRouteReferenceCount: countRule(activeRows, "RECORD_ROUTE"),
    activeExplorationObjectCardReferenceCount: countRule(activeRows, "OBJECT_CARD"),
    activeExplorationObjectTitleReferenceCount: activeRows.filter(
      (row) => row.ruleId === "ARCHIVE_OBJECT_FIELD" && /objectTitle/i.test(row.match),
    ).length,
    activeExplorationObjectThumbnailReferenceCount: activeRows.filter(
      (row) => row.ruleId === "ARCHIVE_OBJECT_FIELD" && /thumbnail/i.test(row.match),
    ).length,
    activeExplorationExternalModelReferenceCount: countRule(activeRows, "EXTERNAL_MODEL_REFERENCE"),
    activeExplorationExternalModelImportCount: countRule(activeRows, "EXTERNAL_MODEL_IMPORT"),
    activeExplorationModelDownloadTargetCount: countRule(activeRows, "MODEL_DOWNLOAD_TARGET"),
    explorationExternalModelDependencyCount: dependencies.external.length,
    explorationVectorDatabaseDependencyCount: dependencies.vector.length,
    activeImplementationViolationCount: activeRows.length,
    legacyExecutionDirCount: legacyExecutionDirsRemaining.length,
    legacyPackageScriptCount: oldPackageScripts.length,
    publicExplorationRouteCount: publicRoutePaths.length,
    sealedEvidenceChangedFileCount: sealedEvidenceChanges.length,
    searchFilesChanged: searchChanges.length,
    contextFilesChanged: contextChanges.length,
    spacetimeFilesChanged: spacetimeChanges.length,
    databaseFilesChanged: databaseChanges.length,
    databaseVersion: databaseFreeze.receipt?.databaseVersion ?? -1,
    databaseUnmanifestedAdditiveFileCount:
      databaseFreeze.receipt?.unmanifestedV49DatabaseFileCount ?? -1,
    databaseFrozenPathDriftCount: databaseFreeze.receipt?.frozenPathDriftCount ?? 1,
    databaseFreezeFailureCount: databaseFreeze.failures.length,
    policyDocumentFailureCount: policyDocuments.failures.length,
  };
  const failures = [
    ...Object.entries(metrics)
      .filter(([key, value]) => !MEASUREMENT_ONLY_METRICS.has(key) && value !== 0)
      .map(([key, value]) => `${key}=${value}`),
    ...databaseFreeze.failures,
  ];
  return {
    status: failures.length === 0 ? "PASS" : "FAIL",
    sourceSha: REQUIRED_SOURCE_SHA,
    metrics,
    failures,
    activeRows,
    dependencyDecisions: {
      externalModelDependencies: dependencies.external,
      vectorDatabaseDependencies: dependencies.vector,
      decision: "No dependency was removed: no superseded Exploration-only package was present in the manifests.",
    },
    policyDocuments: {
      badPracticeRuleCount: policyDocuments.badPracticeRuleCount,
      failures: policyDocuments.failures,
    },
    protectedChanges: {
      search: searchChanges,
      context: contextChanges,
      spacetime: spacetimeChanges,
      database: databaseChanges,
      databaseFreeze: databaseFreeze.receipt,
      sealedEvidence: sealedEvidenceChanges,
    },
    legacyExecutionDirsRemaining,
    oldPackageScripts,
    publicRoutePaths,
  };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = auditActiveRepository();
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (result.status !== "PASS") process.exitCode = 1;
}
