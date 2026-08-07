import Link from "next/link";
import type { CSSProperties } from "react";
import type { FolderTypeKey } from "@/types/archive";

export interface SpeedIndexItem {
  key: string;
  type: FolderTypeKey;
  code: string;
  title: string;
  href: string;
  count: number;
}

export interface SpeedIndexGroup {
  key: FolderTypeKey;
  title: string;
  href: string;
  code: string;
  folderCount: number;
  surfaceCount: number;
  items: SpeedIndexItem[];
}

export default function SpeedIndexHome({ groups }: { groups: SpeedIndexGroup[] }) {
  return (
    <div className="speed-stage">
      <div className="speed-sheet" aria-label="Archive speed index">
        {groups.map((group) => (
          <section
            key={group.key}
            className="speed-group"
            data-folder-type={group.key}
            data-density={group.key === "region" ? "wide" : "standard"}
          >
            <Link href={group.href} className="speed-group__tab">
              <strong>{group.code}</strong>
              <span>{String(group.folderCount).padStart(3, "0")}</span>
            </Link>

            <Link href={group.href} className="speed-group__head">
              <span>{group.title}</span>
              <span>{group.folderCount} folders / {group.surfaceCount} design records</span>
            </Link>

            <div className="speed-mini-stack">
              {group.items.map((item, index) => (
                <Link
                  key={item.key}
                  href={item.href}
                  className="speed-folder"
                  data-folder-type={item.type}
                  style={
                    {
                      "--tab-offset": `${0.36 + (index % 5) * 1.02}rem`,
                      "--tab-offset-right": `${0.42 + (index % 4) * 1.1}rem`,
                    } as CSSProperties
                  }
                >
                  <span
                    className={
                      index % 4 === 2
                        ? "speed-tab speed-tab--right"
                        : "speed-tab speed-tab--left"
                    }
                  >
                    <strong>{item.code}</strong>
                    <span>{String(item.count).padStart(3, "0")}</span>
                  </span>

                  <span className="speed-line speed-line--primary">
                    <strong>{item.title}</strong>
                    <span>{item.count}</span>
                  </span>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
