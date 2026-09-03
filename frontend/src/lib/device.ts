/* Server-side device split (§4a). A page's `page.tsx` calls resolveView() once,
   from the request User-Agent, and renders its desktop/ OR mobile/ tree — never
   both, no client swap. Coarse by design; tablets resolve to desktop. A ?view=
   query param overrides it, for QA and for a "view desktop site" link. */

export type PageView = "mobile" | "desktop";

const MOBILE_UA =
  /Android|webOS|iPhone|iPod|BlackBerry|BB10|IEMobile|Opera Mini|Windows Phone|Mobile Safari/i;

/** Coarse: phones → true; iPad and other tablets → false (desktop tree). */
export function isMobileUA(ua: string | null | undefined): boolean {
  if (!ua) return false;
  if (/iPad|Tablet/i.test(ua)) return false;
  return MOBILE_UA.test(ua);
}

/** `view` wins when it is an explicit "mobile" | "desktop"; otherwise sniff UA. */
export function resolveView(
  view: string | string[] | undefined,
  ua: string | null | undefined,
): PageView {
  const v = Array.isArray(view) ? view[0] : view;
  if (v === "mobile" || v === "desktop") return v;
  return isMobileUA(ua) ? "mobile" : "desktop";
}
