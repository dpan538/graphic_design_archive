import "server-only";

import type { ArchiveRepositoryProvider } from "../repository";
import { FixtureArchiveRepositoryProvider } from "./fixture";

/** Server-only composition root. There is no browser fallback or mode probing. */
export function getArchiveRepositoryProvider(): ArchiveRepositoryProvider {
  const mode = process.env.ARCHIVE_REPOSITORY_MODE;
  if (mode === "fixture") {
    if (process.env.NODE_ENV === "production") throw new Error("fixture repository is forbidden in production");
    return new FixtureArchiveRepositoryProvider();
  }
  throw new Error("ARCHIVE_REPOSITORY_MODE must explicitly select a configured production repository");
}
