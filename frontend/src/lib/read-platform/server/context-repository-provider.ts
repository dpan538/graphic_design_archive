import "server-only";

import type { PublicContextDataset } from "@/features/trace-v49/context/governed/types";
import type { ArchiveRepository, ArchiveRepositoryProvider } from "../repository";
import type {
  ReadOptions,
  RepoResult,
  ResearchReleaseSelector,
  VisualRegistrySelector,
} from "../types";

function failure<T>(
  code: "UNAVAILABLE" | "INTEGRITY_FAILURE",
  message: string,
): RepoResult<T> {
  return Object.freeze({
    ok: false as const,
    error: Object.freeze({ code, message, retryable: code === "UNAVAILABLE" }),
  });
}

function withGovernedContext(repository: ArchiveRepository): ArchiveRepository {
  const getTraceContext = async (
    objectId: string,
    options?: ReadOptions,
  ): Promise<RepoResult<PublicContextDataset>> => {
    if (options?.signal?.aborted) return failure("UNAVAILABLE", "request was cancelled");
    try {
      const { lookupGovernedContextDataset } = await import(
        "@/features/trace-v49/context/governed/reader.server"
      );
      if (options?.signal?.aborted) return failure("UNAVAILABLE", "request was cancelled");
      const result = lookupGovernedContextDataset(objectId, {
        researchReleaseId: repository.version.research.researchReleaseId,
        researchManifestSha256: repository.version.research.researchManifestSha256,
      });
      return result.ok
        ? Object.freeze({ ok: true as const, data: result.data, version: repository.version })
        : Object.freeze({
          ok: false as const,
          error: Object.freeze({ code: result.code, message: result.message, retryable: false }),
        });
    } catch {
      return failure("INTEGRITY_FAILURE", "the governed Context projection failed validation");
    }
  };
  return new Proxy(repository, {
    get(target, property, receiver) {
      if (property === "getTraceContext") return getTraceContext;
      const value = Reflect.get(target, property, receiver) as unknown;
      return typeof value === "function" ? value.bind(target) : value;
    },
  });
}

export class GovernedContextArchiveRepositoryProvider implements ArchiveRepositoryProvider {
  constructor(private readonly delegate: ArchiveRepositoryProvider) {}

  async open(
    input: Readonly<{
      research: ResearchReleaseSelector;
      visual?: VisualRegistrySelector | null;
    }>,
    options?: ReadOptions,
  ): Promise<RepoResult<ArchiveRepository>> {
    const opened = await this.delegate.open(input, options);
    if (!opened.ok) return opened;
    return Object.freeze({
      ok: true as const,
      data: withGovernedContext(opened.data),
      version: opened.version,
    });
  }
}
