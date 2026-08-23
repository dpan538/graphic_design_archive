import "server-only";

import type { ArchiveRepositoryProvider } from "../repository";
import { DerivedV49ArchiveRepositoryProvider } from "@/features/search-v49/server/derived-repository";
import { GovernedContextArchiveRepositoryProvider } from "./context-repository-provider";
import { FixtureArchiveRepositoryProvider } from "./fixture";

/** Server-only composition root. There is no browser fallback or mode probing. */
export function getArchiveRepositoryProvider(): ArchiveRepositoryProvider {
  const mode = process.env.ARCHIVE_REPOSITORY_MODE;
  if (mode === "fixture") {
    if (process.env.NODE_ENV === "production") throw new Error("fixture repository is forbidden in production");
    return new FixtureArchiveRepositoryProvider();
  }
  if (!mode || mode === "derived-v49") {
    return new GovernedContextArchiveRepositoryProvider(
      new DerivedV49ArchiveRepositoryProvider(),
    );
  }
  throw new Error("ARCHIVE_REPOSITORY_MODE must be derived-v49 or the non-production fixture mode");
}
