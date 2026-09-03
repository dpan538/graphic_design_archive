import { Suspense } from "react";
import { headers } from "next/headers";
import { resolveView } from "@/lib/device";
import SearchDesktop from "@/app/search/desktop/SearchDesktop";
import SearchMobile from "@/app/search/mobile/SearchMobile";

/* Search opened from inside the app, layered over the page you were already
   on. The panel was always built as a modal — position:fixed, its own scrim,
   Close = history.back() — but it only existed at its own route, so reaching
   it from the homepage replaced the homepage with an empty page and left the
   panel floating over nothing. Intercepting the navigation keeps the host
   page mounted underneath; a direct visit or refresh of /search still gets
   the standalone page, so deep links and the product's Search route are
   unchanged. */
export default async function SearchModal() {
  const view = resolveView(undefined, (await headers()).get("user-agent"));

  return (
    <Suspense fallback={null}>
      {view === "mobile" ? (
        /* The mobile treatment is a full page, not a floating panel, so it
           has to be lifted into an overlay to cover the host page. */
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 60,
            overflowY: "auto",
            background: "var(--paper)",
          }}
        >
          <SearchMobile />
        </div>
      ) : (
        <SearchDesktop asModal />
      )}
    </Suspense>
  );
}
