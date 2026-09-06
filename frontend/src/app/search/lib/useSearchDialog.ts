"use client";

import { useEffect, useRef, type RefObject } from "react";

export function useSearchDialog(card: RefObject<HTMLElement | null>, close: () => void) {
  const returnFocus = useRef<HTMLElement | null>(typeof document === "undefined" ? null : document.activeElement as HTMLElement);
  const onClose = useRef(close);
  onClose.current = close;
  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); onClose.current(); return; }
      if (event.key !== "Tab") return;
      const nodes = Array.from(card.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex="0"]') ?? [])
        .filter((node) => node.getClientRects().length > 0);
      const first = nodes[0], last = nodes.at(-1);
      if (!first || !last) return;
      if (!card.current?.contains(document.activeElement) || (event.shiftKey ? document.activeElement === first : document.activeElement === last)) {
        event.preventDefault(); (event.shiftKey ? last : first).focus();
      }
    };
    document.addEventListener("keydown", keydown);
    return () => {
      document.removeEventListener("keydown", keydown);
      document.body.style.overflow = previousOverflow;
      const target = returnFocus.current;
      requestAnimationFrame(() => {
        const opener = target?.isConnected && target !== document.body ? target : document.querySelector<HTMLElement>('nav a[aria-label="Search"]');
        if (window.location.pathname !== "/search") opener?.focus({ preventScroll: true });
      });
    };
  }, [card]);
}
