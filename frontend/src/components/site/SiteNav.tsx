"use client";

import type { ComponentType, SVGProps } from "react";
import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Info, Link2, Search, TableOfContents, Waypoints } from "lucide-react";
import styles from "./SiteNav.module.css";

export type SiteNavKey = "index" | "trace" | "search" | "about" | "source";
export type SiteNavVariant = "desktop" | "mobile";

type IconType = ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }>;

type NavItem = {
  key: SiteNavKey;
  label: string;
  /* What the hover reveal prints. TRACE is the product's canonical name and
     stays the accessible label, but set all-caps beside "Index" / "Search" it
     reads a size larger than its siblings even at identical type. */
  reveal?: string;
  href: string;
  Icon: IconType;
  /* Absent from the mobile bar — see §4a. Mobile nav is MGDA · Index · About. */
  mobileHide?: boolean;
};

/* Top-right order, per the IA: Index · TRACE · Search · About · Source.
   Icons: Index = a contents/directory mark (not a bookshelf), About = an "i",
   Source = a link (it points out to original sources, not "read"/"index"). */
const ITEMS: NavItem[] = [
  { key: "index", label: "Index", href: "/directory", Icon: TableOfContents },
  { key: "trace", label: "TRACE", reveal: "Trace", href: "/trace", Icon: Waypoints, mobileHide: true },
  { key: "search", label: "Search", href: "/search", Icon: Search },
  { key: "about", label: "About", href: "/about", Icon: Info },
  { key: "source", label: "Source", href: "/source", Icon: Link2, mobileHide: true },
];

export default function SiteNav({
  active,
  variant = "desktop",
  revealTone = "light",
}: {
  active?: SiteNavKey;
  variant?: SiteNavVariant;
  /* Colour of the hover/focus destination label (§ below) — it sits directly
     on the page content under the header, not on a background of its own, so
     it needs to know whether that content is light (cream, most pages — ink
     text) or dark (this homepage's hero ground — paper-cream text) to stay
     legible. */
  revealTone?: "light" | "dark";
}) {
  const mobile = variant === "mobile";
  const pathname = usePathname();
  const router = useRouter();
  const [revealed, setRevealed] = useState<NavItem | null>(null);
  // The mobile path ships only its three items — no hidden DOM, no hover reveal.
  const items = mobile ? ITEMS.filter((i) => !i.mobileHide) : ITEMS;

  return (
    <header className={styles.header} data-variant={variant}>
      <Link href="/" className={styles.brand} aria-label="Modern Graphic Design Archive — home">
        <span className={styles.monogram} aria-hidden="true">MGDA</span>
        <span className={styles.wordmark}>
          <span>Modern Graphic Design</span>
          <span>Archive</span>
        </span>
      </Link>

      <nav className={styles.nav} aria-label="Primary">
        <ul className={styles.list} role="list">
          {items.map((item) => {
            const isActive = item.key === active;
            /* Search is a panel, so its control toggles: pressing it again
               while the panel is open closes it rather than re-navigating to
               the route it is already on. Closing is history.back(), the same
               action the panel's own close button and scrim use, so the page
               underneath is restored instead of pushed over again. */
            const isOpenPanel = item.key === "search" && pathname === "/search";
            const hover = mobile
              ? undefined
              : {
                  onMouseEnter: () => setRevealed(item),
                  onMouseLeave: () =>
                    setRevealed((cur) => (cur?.key === item.key ? null : cur)),
                  onFocus: () => setRevealed(item),
                  onBlur: () =>
                    setRevealed((cur) => (cur?.key === item.key ? null : cur)),
                };
            return (
              <li key={item.key}>
                <Link
                  href={item.href}
                  className={styles.control}
                  aria-label={item.label}
                  aria-current={isActive ? "page" : undefined}
                  aria-expanded={item.key === "search" ? isOpenPanel : undefined}
                  data-active={isActive || undefined}
                  onClick={
                    isOpenPanel
                      ? (e) => {
                          e.preventDefault();
                          router.back();
                        }
                      : undefined
                  }
                  {...hover}
                >
                  <item.Icon size={33} strokeWidth={2.75} aria-hidden="true" />
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {!mobile ? (
        /* Decorative: hovered/focused destination name, in the empty page space. */
        <div
          className={styles.reveal}
          aria-hidden="true"
          data-shown={revealed ? "true" : "false"}
          data-tone={revealTone}
        >
          <span>{revealed ? (revealed.reveal ?? revealed.label) : ""}</span>
        </div>
      ) : null}
    </header>
  );
}
