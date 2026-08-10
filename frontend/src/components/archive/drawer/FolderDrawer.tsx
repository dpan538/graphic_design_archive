import Link from "next/link";
import type { FolderTypeKey } from "@/types/archive";

export interface DrawerItem {
  key: string;
  type?: FolderTypeKey;
  ink?: string;
  tabLabel: string;
  title: string;
  href: string;
  reveal: string[];
}

function ItemMarker({ type }: { type?: FolderTypeKey }) {
  return (
    <span
      className="cabinet-item-marker"
      data-folder-type={type ?? "unknown"}
      aria-hidden="true"
    />
  );
}

/**
 * Two deliberately separate entrances to one research index:
 * a compact coordinate table for large screens, and a native vertical card
 * wheel for touch screens. They share routes and data, not mechanics.
 */
export default function FolderDrawer({ items }: { items: DrawerItem[] }) {
  return (
    <div className="drawer-stage">
      <section className="research-coordinate-index" aria-label="Research coordinates">
        <header className="research-coordinate-index__intro">
          <p className="label-caps">
            Research index · {String(items.length).padStart(2, "0")} coordinates
          </p>
          <p>
            Read the archive through four intersecting catalogue structures.
            Every route preserves object and source evidence.
          </p>
        </header>

        <div className="research-coordinate-index__frame">
          <nav className="research-coordinate-index__rows" aria-label="Primary archive coordinates">
            {items.map((item, index) => (
              <Link
                key={item.key}
                href={item.href}
                className="research-coordinate-row"
                data-folder-type={item.type ?? "unknown"}
              >
                <span className="research-coordinate-row__index" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <ItemMarker type={item.type} />
                <span className="research-coordinate-row__title">{item.title}</span>
                <span className="research-coordinate-row__count">{item.reveal[1]}</span>
                <span className="research-coordinate-row__action" aria-hidden="true">
                  inspect ↓
                </span>
                <span className="research-coordinate-row__scope">{item.reveal[0]}</span>
              </Link>
            ))}
          </nav>
        </div>
      </section>

      <section className="mobile-card-wheel" aria-label="Archive coordinate card wheel">
        <div
          className="mobile-card-wheel__viewport"
          role="region"
          aria-label="Vertical archive coordinate cards"
          tabIndex={0}
        >
          <div className="mobile-card-wheel__track">
            {items.map((item, index) => (
              <Link
                key={item.key}
                href={item.href}
                className="wheel-card"
                data-folder-type={item.type ?? "unknown"}
              >
                <span className="wheel-card__rail">
                  <span className="wheel-card__index" aria-hidden="true">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <ItemMarker type={item.type} />
                  <span>{item.tabLabel}</span>
                </span>
                <span className="wheel-card__title">{item.title}</span>
                <span className="wheel-card__scope">{item.reveal[0]}</span>
                <span className="wheel-card__count">{item.reveal[1]}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
