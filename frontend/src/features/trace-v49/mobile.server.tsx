import "server-only";

import { headers } from "next/headers";

export async function isLikelyMobileTraceRequest(): Promise<boolean> {
  const requestHeaders = await headers();
  if (requestHeaders.get("sec-ch-ua-mobile") === "?1") return true;
  const userAgent = requestHeaders.get("user-agent") ?? "";
  return /Android|iPhone|iPad|iPod|Mobile|Windows Phone/i.test(userAgent);
}

export function TraceDesktopRequired({ functionName = "TRACE" }: { functionName?: string }) {
  return (
    <main className="read-platform">
      <p className="read-platform__eyebrow">Desktop research environment</p>
      <h1>{functionName} requires a desktop viewport</h1>
      <p>Global Search remains available on this device. TRACE is a full research environment and is not compressed into a reduced mobile mode.</p>
      <a href="/search">Open Global Search</a>
    </main>
  );
}
