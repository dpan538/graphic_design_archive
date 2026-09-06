"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Info, Search, TableOfContents } from "lucide-react";
import styles from "./SiteNavMobile.module.css";

export type SiteNavMobileKey = "index" | "search" | "about";

/* The mobile bar (§4a, owner 2026-09-06): the MGDA tile and three icon
   controls — Index · Search · About. No wordmark, no TRACE, no Source (Source
   lives inside About on the phone). Pressing Search while the Search window
   is open closes it (history.back), as on the desktop. This file is the
   mobile path's own; the desktop nav is not imported here. */
export default function SiteNavMobile({ active }: { active?: SiteNavMobileKey }) {
  const pathname = usePathname();
  const router = useRouter();
  const searchOpen = pathname === "/search";
  const items: { key: SiteNavMobileKey; label: string; href: string; Icon: typeof Info }[] = [
    { key: "index", label: "Index", href: "/directory", Icon: TableOfContents },
    { key: "search", label: "Search", href: "/search", Icon: Search },
    { key: "about", label: "About", href: "/about", Icon: Info },
  ];
  return (
    <header className={styles.header} data-nav="mobile">
      <Link href="/" className={styles.monogram} aria-label="Modern Graphic Design Archive — home">MGDA</Link>
      <nav aria-label="Primary">
        <ul className={styles.list} role="list">
          {items.map((item) => (
            <li key={item.key}>
              <Link
                href={item.href}
                className={styles.control}
                aria-label={item.label}
                aria-current={item.key === active ? "page" : undefined}
                aria-expanded={item.key === "search" ? searchOpen : undefined}
                data-active={item.key === active || undefined}
                scroll={item.key !== "search"}
                onClick={item.key === "search" && searchOpen ? (event) => { event.preventDefault(); router.back(); } : undefined}
              >
                <item.Icon size={26} strokeWidth={2.75} aria-hidden="true" />
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
