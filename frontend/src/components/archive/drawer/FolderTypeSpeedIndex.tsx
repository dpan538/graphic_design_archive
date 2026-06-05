import Link from "next/link";
import type { CSSProperties } from "react";
import type { FolderType, FolderTypeKey } from "@/types/archive";

export interface FolderTypeSpeedItem {
  key: string;
  type: FolderTypeKey;
  macroLabel?: string;
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
  const macroGroups =
    folderType.type === "region"
      ? items.reduce<
          { label: string; groups: { label: string; items: FolderTypeSpeedItem[] }[] }[]
        >((acc, item) => {
          const macro = item.macroLabel ?? "Other";
          const groupLabel = item.groupLabel ?? "Other regions";
          let macroGroup = acc.find((group) => group.label === macro);
          if (!macroGroup) {
            macroGroup = { label: macro, groups: [] };
            acc.push(macroGroup);
          }
          const existing = macroGroup.groups.find((group) => group.label === groupLabel);
          if (existing) existing.items.push(item);
          else macroGroup.groups.push({ label: groupLabel, items: [item] });
          return acc;
        }, [])
      : [{ label: "", groups: [{ label: "", items }] }];
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
            {macroGroups.map((macroGroup) => (
              <section className="folder-cut-macro" key={macroGroup.label || folderType.type}>
                {macroGroup.label ? <h2 className="folder-cut-macro__label">{macroGroup.label}</h2> : null}
                {macroGroup.groups.map((group) => (
                  <div className="folder-cut-group" key={`${macroGroup.label}-${group.label}`}>
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
              </section>
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
