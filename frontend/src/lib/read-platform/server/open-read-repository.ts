import "server-only";

import { getArchiveRepositoryProvider } from "./provider";
import type { ArchiveRepository } from "../repository";

/** Resolve `current` once at the server boundary.  All repository methods then
 * operate on the returned immutable research release pair. */
export async function openCurrentReadRepository(): Promise<ArchiveRepository> {
  const result = await getArchiveRepositoryProvider().open({ research: { alias: "current" } });
  if (!result.ok) throw new Error(`${result.error.code}: ${result.error.message}`);
  return result.data;
}
