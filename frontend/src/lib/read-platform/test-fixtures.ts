/** Test-only adversarial data.  It is intentionally not imported by any route,
 * provider, or production fixture.  The sentinel lets leak tests prove that a
 * held locator never crosses the public boundary. */
export const HELD_SENTINEL_URL = "https://held.invalid/v49-fixture-never-public.png";

export function createSyntheticReadCases() {
  if (process.env.NODE_ENV !== "test") throw new Error("synthetic read cases are test-only");
  return {
    synthetic: true,
    remoteImage: { synthetic: true, url: "https://synthetic.invalid/remote-image.png" },
    traceObject: { synthetic: true, totalExact: 1 },
    unknownRelation: { synthetic: true, code: "unknown_relation" },
    takedown: { synthetic: true, heldLocator: HELD_SENTINEL_URL },
  } as const;
}
