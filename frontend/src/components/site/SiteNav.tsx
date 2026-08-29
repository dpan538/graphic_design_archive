"use client";

import type { ComponentType, SVGProps } from "react";
import { useState } from "react";
import Link from "next/link";
import { BookOpen, Library, ScrollText, Search, Waypoints } from "lucide-react";
import styles from "./SiteNav.module.css";

export type SiteNavKey = "index" | "trace" | "search" | "about" | "source";

type IconType = ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }>;

type NavItem = {
  key: SiteNavKey;
  label: string;
  href: string;
  Icon: IconType;
};

/* Top-right order, per the IA: Index · TRACE · Search · About · Source. */
const ITEMS: NavItem[] = [
  { key: "index", label: "Index", href: "/index", Icon: Library },
  { key: "trace", label: "TRACE", href: "/trace", Icon: Waypoints },
  { key: "search", label: "Search", href: "/search", Icon: Search },
  { key: "about", label: "About", href: "/about", Icon: BookOpen },
  { key: "source", label: "Source", href: "/source", Icon: ScrollText },
];

export default function SiteNav({ active }: { active?: SiteNavKey }) {
  const [revealed, setRevealed] = useState<NavItem | null>(null);

  return (
    <header className={styles.header}>
      <Link href="/" className={styles.brand} aria-label="Modern Graphic Design Archive — home">
        <span className={styles.monogram} aria-hidden="true">MGDA</span>
        <span className={styles.wordmark}>
          <span>Modern Graphic Design</span>
          <span>Archive</span>
        </span>
      </Link>

      <nav className={styles.nav} aria-label="Primary">
        <ul className={styles.list} role="list">
          {ITEMS.map((item) => {
            const isActive = item.key === active;
            return (
              <li key={item.key}>
                <Link
                  href={item.href}
                  className={styles.control}
                  aria-label={item.label}
                  aria-current={isActive ? "page" : undefined}
                  data-active={isActive || undefined}
                  onMouseEnter={() => setRevealed(item)}
                  onMouseLeave={() =>
                    setRevealed((cur) => (cur?.key === item.key ? null : cur))
                  }
                  onFocus={() => setRevealed(item)}
                  onBlur={() =>
                    setRevealed((cur) => (cur?.key === item.key ? null : cur))
                  }
                >
                  <item.Icon size={33} strokeWidth={2.75} aria-hidden="true" />
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Decorative: hovered/focused destination name, in the empty page space. */}
      <div
        className={styles.reveal}
        aria-hidden="true"
        data-shown={revealed ? "true" : "false"}
      >
        <span>{revealed?.label ?? ""}</span>
      </div>
    </header>
  );
}
