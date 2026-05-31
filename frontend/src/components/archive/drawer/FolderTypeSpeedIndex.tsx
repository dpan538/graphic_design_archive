import Link from "next/link";
import type { CSSProperties } from "react";
import type { FolderType, FolderTypeKey } from "@/types/archive";

export interface FolderTypeSpeedItem {
  key: string;
  type: FolderTypeKey;
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

  return (
    <div className="folder-type-stage">
      <section
        className="folder-type-stack"
        data-folder-type={folderType.type}
        data-density={folderType.type === "region" ? "wide" : "standard"}
      >
        {items.length > 0 ? (
          <div className="folder-type-stack__cuts">
            {items.map((item, index) => (
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
