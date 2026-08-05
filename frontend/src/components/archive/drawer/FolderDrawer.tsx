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
 * Two deliberately separate entrances to one archive index:
 * a compact filing-cabinet menu for large screens, and a native vertical
 * card wheel for touch screens. They share routes and data, not mechanics.
 */
export default function FolderDrawer({ items }: { items: DrawerItem[] }) {
  return (
    <div className="drawer-stage">
      <section className="cabinet-menu" aria-labelledby="cabinet-menu-title">
        <header className="cabinet-menu__intro">
          <div>
            <p className="label-caps">
              Archive cabinet · {String(items.length).padStart(2, "0")} coordinates
            </p>
            <h1 id="cabinet-menu-title">Open the archive cabinet.</h1>
          </div>
          <p>
            Choose one catalogue coordinate. Every entry returns to the same
            evidence collection.
          </p>
        </header>

        <div className="cabinet-menu__case">
          <nav className="cabinet-menu__rows" aria-label="Primary archive coordinates">
            {items.map((item, index) => (
              <Link
                key={item.key}
                href={item.href}
                className="cabinet-row"
                data-folder-type={item.type ?? "unknown"}
              >
                <span className="cabinet-row__index" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <ItemMarker type={item.type} />
                <span className="cabinet-row__title">{item.title}</span>
                <span className="cabinet-row__count">{item.reveal[1]}</span>
                <span className="cabinet-row__action" aria-hidden="true">
                  open ↓
                </span>
                <span className="cabinet-row__scope">{item.reveal[0]}</span>
              </Link>
            ))}
          </nav>

          <div className="cabinet-menu__drawer-front" aria-hidden="true">
            <span>MGDH / CABINET 01</span>
            <span className="cabinet-menu__handle">OPEN</span>
            <span>PRIMARY INDEX</span>
          </div>
        </div>
      </section>

      <section className="mobile-card-wheel" aria-label="Archive coordinate card wheel">
        <header className="mobile-card-wheel__intro">
          <p className="label-caps">
            Browse · {String(items.length).padStart(2, "0")} coordinates
          </p>
          <h1 id="mobile-wheel-title">Move through the index.</h1>
        </header>

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
                <span className="wheel-card__action">tap to open →</span>
              </Link>
            ))}
          </div>
        </div>

        <p className="mobile-card-wheel__instruction label-caps">
          Scroll up / down · the centred card is active
        </p>
      </section>
    </div>
  );
}
