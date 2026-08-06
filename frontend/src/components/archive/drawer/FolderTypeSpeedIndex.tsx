"use client";

import Link from "next/link";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type UIEvent,
} from "react";
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
  dateStart: number;
  dateEnd: number;
  date: string;
  mix: string;
}

const PERIODS = [
  { id: "all", label: "All periods", start: -Infinity, end: Infinity },
  { id: "pre1900", label: "Before 1900", start: -Infinity, end: 1899 },
  { id: "1900-1944", label: "1900–1944", start: 1900, end: 1944 },
  { id: "1945-1979", label: "1945–1979", start: 1945, end: 1979 },
  { id: "1980-now", label: "1980–present", start: 1980, end: Infinity },
] as const;

export default function FolderTypeSpeedIndex({
  folderType,
  items,
}: {
  folderType: FolderType;
  items: FolderTypeSpeedItem[];
}) {
  const [continent, setContinent] = useState("all");
  const [period, setPeriod] = useState<(typeof PERIODS)[number]["id"]>("all");
  const [activeCard, setActiveCard] = useState(1);
  const cardWheelRef = useRef<HTMLElement | null>(null);
  const cardScrollFrame = useRef<number | null>(null);
  const isRegion = folderType.type === "region";
  const primaryItems = useMemo(
    () => isRegion ? items.filter((item) => item.macroLabel !== "Unresolved") : items,
    [isRegion, items],
  );
  const isolatedReviewCount = items.length - primaryItems.length;
  const continents = useMemo(
    () => Array.from(new Set(primaryItems.map((item) => item.macroLabel).filter(Boolean) as string[])),
    [primaryItems],
  );
  const filteredItems = useMemo(() => {
    const periodFilter = PERIODS.find((entry) => entry.id === period) ?? PERIODS[0];
    return primaryItems.filter((item) => {
      const continentMatch = continent === "all" || item.macroLabel === continent;
      const periodMatch = item.dateEnd >= periodFilter.start && item.dateStart <= periodFilter.end;
      return continentMatch && periodMatch;
    });
  }, [continent, period, primaryItems]);
  const tabOffsets = [0, 50, 0, 33, 66, 0, 25, 50, 75, 0, 20, 40, 60, 80];
  const macroGroups =
    isRegion
      ? filteredItems.reduce<
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
      : [{ label: "", groups: [{ label: "", items: filteredItems }] }];
  let stackIndex = 0;

  useEffect(() => {
    const wheel = cardWheelRef.current;
    if (!wheel || !window.matchMedia("(max-width: 760px)").matches) return;
    const initialIndex = filteredItems.length > 1 ? 1 : 0;
    const target = wheel.children[initialIndex] as HTMLElement | undefined;
    if (!target) return;
    setActiveCard(initialIndex);
    const frame = window.requestAnimationFrame(() => {
      wheel.scrollTop = Math.max(0, target.offsetTop - (wheel.clientHeight - target.offsetHeight) / 2);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [filteredItems]);

  useEffect(() => () => {
    if (cardScrollFrame.current !== null) window.cancelAnimationFrame(cardScrollFrame.current);
  }, []);

  function handleCardWheelScroll(event: UIEvent<HTMLElement>) {
    const wheel = event.currentTarget;
    if (cardScrollFrame.current !== null) window.cancelAnimationFrame(cardScrollFrame.current);
    cardScrollFrame.current = window.requestAnimationFrame(() => {
      const first = wheel.children[0] as HTMLElement | undefined;
      const second = wheel.children[1] as HTMLElement | undefined;
      if (!first) return;
      const pitch = second ? second.offsetTop - first.offsetTop : first.offsetHeight;
      const centered = wheel.scrollTop + wheel.clientHeight / 2;
      const index = Math.round((centered - first.offsetTop - first.offsetHeight / 2) / Math.max(1, pitch));
      setActiveCard(Math.max(0, Math.min(filteredItems.length - 1, index)));
    });
  }

  return (
    <div className="folder-type-stage">
      <section
        className="folder-type-stack"
        data-folder-type={folderType.type}
        data-density={folderType.type === "region" ? "wide" : "standard"}
      >
        {filteredItems.length > 0 ? (
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
                            <span>{isRegion ? "catalogued records" : item.mix}</span>
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

      <nav
        ref={cardWheelRef}
        className="region-card-stack"
        aria-label={`Filtered ${folderType.label.toLowerCase()} folder cards`}
        onScroll={handleCardWheelScroll}
      >
        {filteredItems.length > 0 ? filteredItems.map((item, index) => {
          const distance = Math.abs(index - activeCard);
          if (distance > 2) {
            return (
              <span
                key={item.key}
                className="region-card-stack__spacer"
                aria-hidden="true"
              />
            );
          }
          return (
            <Link
              key={item.key}
              href={item.href}
              className="region-card-stack__card"
              data-position={index === activeCard ? "active" : index < activeCard ? "previous" : "next"}
              data-distance={distance}
              style={{ ["--stack-index" as string]: index + 1 } as CSSProperties}
            >
              <span className="region-card-stack__rail">
                <span>{String(index + 1).padStart(2, "0")}</span>
                <span>{isRegion ? item.macroLabel : folderType.label}</span>
                <span>{isRegion ? item.groupLabel : "research folder"}</span>
              </span>
              <strong>{item.title}</strong>
              <span className="region-card-stack__meta">{item.date}</span>
              <span className="region-card-stack__count">{item.count.toLocaleString("en-US")} indexed records</span>
            </Link>
          );
        }) : (
          <p className="region-card-stack__empty">
            No {folderType.label.toLowerCase()} folders match these filters.
          </p>
        )}
      </nav>

      <details
        className={`folder-type-filters ${isRegion ? "folder-type-filters--region" : "folder-type-filters--period"}`}
      >
        <summary aria-label={`Open filters for ${folderType.label.toLowerCase()} folders`}>
          <span className="label-caps">{folderType.label} filters</span>
          <strong>{filteredItems.length}</strong>
          <span>of {primaryItems.length} active research folders</span>
          <i aria-hidden="true">+</i>
        </summary>
        <div className="folder-type-filters__body">
          {isRegion ? (
            <fieldset>
              <legend>Continent</legend>
              <div className="folder-filter-chips">
                {["all", ...continents].map((value) => (
                  <button
                    key={value}
                    type="button"
                    aria-pressed={continent === value}
                    onClick={() => setContinent(value)}
                  >
                    {value === "all" ? "All" : value}
                  </button>
                ))}
              </div>
            </fieldset>
          ) : null}
          <label>
            Period
            <select value={period} onChange={(event) => setPeriod(event.target.value as typeof period)}>
              {PERIODS.map((entry) => (
                <option key={entry.id} value={entry.id}>{entry.label}</option>
              ))}
            </select>
          </label>
          {(continent !== "all" || period !== "all") ? (
            <button
              type="button"
              className="folder-filter-reset"
              onClick={() => {
                setContinent("all");
                setPeriod("all");
              }}
            >
              Reset filters
            </button>
          ) : null}
          {isolatedReviewCount > 0 ? (
            <p className="folder-filter-isolation">
              {isolatedReviewCount} review / unknown route isolated from the active stack
            </p>
          ) : null}
        </div>
      </details>
    </div>
  );
}
