import Link from "next/link";
import type { CSSProperties } from "react";
import type { FolderType, FolderTypeKey } from "@/types/archive";

export interface FolderTypeSpeedItem {
  key: string;
  type: FolderTypeKey;
  groupLabel?: string;
  code: string;
  title: string;
  href: string;
  count: number;
  date: string;
  mix: string;
}

export default function FolderTypeSpeedIndex({
  folderType,
  items,
}: {
  folderType: FolderType;
  items: FolderTypeSpeedItem[];
}) {
  const tabOffsets = [0, 50, 0, 33, 66, 0, 25, 50, 75, 0, 20, 40, 60, 80];
  const groups =
    folderType.type === "region"
      ? items.reduce<{ label: string; items: FolderTypeSpeedItem[] }[]>((acc, item) => {
          const label = item.groupLabel ?? "Other regions";
          const existing = acc.find((group) => group.label === label);
          if (existing) existing.items.push(item);
          else acc.push({ label, items: [item] });
          return acc;
        }, [])
      : [{ label: "", items }];
  let stackIndex = 0;

  return (
    <div className="folder-type-stage">
      <section
        className="folder-type-stack"
        data-folder-type={folderType.type}
        data-density={folderType.type === "region" ? "wide" : "standard"}
      >
        {items.length > 0 ? (
          <div className="folder-type-stack__cuts">
            {groups.map((group) => (
              <div className="folder-cut-group" key={group.label || folderType.type}>
                {group.label ? <p className="folder-cut-group__label">{group.label}</p> : null}
                {group.items.map((item) => {
                  const index = stackIndex++;
                  return (
                    <Link
                      key={item.key}
                      href={item.href}
                      className="folder-cut"
                      style={
                        {
                          "--tab-left": `${tabOffsets[index % tabOffsets.length]}%`,
                          "--stack-index": index + 1,
                        } as CSSProperties
                      }
                    >
                      <span className="folder-cut__tab">
                        <strong>{item.title}</strong>
                        <span>{item.code}</span>
                      </span>

                      <span className="folder-cut__rail">
                        <span>{item.date}</span>
                        <strong>{String(item.count).padStart(3, "0")}</strong>
                        <span>{item.mix}</span>
                      </span>
                    </Link>
                  );
                })}
              </div>
            ))}
          </div>
        ) : (
          <div className="folder-cut folder-cut--empty">
            <p className="label-caps">No folders indexed</p>
            <p>
              This drawer is reserved for named design movements and schools
              once source evidence is strong enough to support folder creation.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
