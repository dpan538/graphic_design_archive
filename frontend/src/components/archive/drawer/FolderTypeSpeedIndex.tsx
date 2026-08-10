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

function cardWheelViewportHeight(wheel: HTMLElement) {
  const stage = wheel.parentElement;
  if (!stage) return wheel.clientHeight;
  const filter = stage.querySelector<HTMLElement>(".folder-type-filters");
  const style = window.getComputedStyle(stage);
  const padding =
    Number.parseFloat(style.paddingTop) + Number.parseFloat(style.paddingBottom);
  const gap = Number.parseFloat(style.rowGap) || 0;
  return Math.max(
    1,
    stage.clientHeight - padding - gap - (filter?.offsetHeight ?? 0),
  );
}

/**
 * Map the native scroll position directly onto the card geometry. This keeps
 * touch movement one-to-one with the finger instead of replaying a desktop
 * hover transition after the gesture has ended.
 */
function updateCardWheelGeometry(wheel: HTMLElement) {
  const children = Array.from(wheel.children) as HTMLElement[];
  const first = children[0];
  const second = children[1];
  if (!first) return 0;

  const pitch = Math.max(
    1,
    second ? second.offsetTop - first.offsetTop : first.offsetHeight,
  );
  // Keep one complete predecessor above the active card. A viewport-centred
  // focus left a large, apparently empty area at the top of compact screens.
  const viewportHeight = cardWheelViewportHeight(wheel);
  const focusLine = Math.min(viewportHeight / 2, pitch * 1.55);
  const viewportCenter = wheel.scrollTop + focusLine;
  let nearestIndex = 0;
  let nearestDistance = Number.POSITIVE_INFINITY;

  children.forEach((child, index) => {
    const cardCenter = child.offsetTop + child.offsetHeight / 2;
    const offset = (cardCenter - viewportCenter) / pitch;
    const distance = Math.abs(offset);
    if (distance < nearestDistance) {
      nearestDistance = distance;
      nearestIndex = index;
    }

    if (!child.classList.contains("region-card-stack__card")) return;
    const clamped = Math.max(-2.25, Math.min(2.25, offset));
    const magnitude = Math.abs(clamped);
    child.style.setProperty("--wheel-rotate", `${clamped * 18}deg`);
    child.style.setProperty("--wheel-depth", `${8 - magnitude * 48}px`);
    child.style.setProperty("--wheel-scale", String(Math.max(0.84, 1 - magnitude * 0.055)));
    child.style.setProperty("--wheel-opacity", String(Math.max(0.26, 1 - magnitude * 0.22)));
    child.style.setProperty("--wheel-saturation", String(Math.max(0.52, 1.08 - magnitude * 0.2)));
  });

  return nearestIndex;
}

function prepareCardWheel(wheel: HTMLElement) {
  const sample = wheel.querySelector<HTMLElement>(".region-card-stack__card");
  if (!sample) return;
  const children = Array.from(wheel.children) as HTMLElement[];
  const second = children[1];
  const pitch = Math.max(
    1,
    second ? second.offsetTop - children[0].offsetTop : sample.offsetHeight,
  );
  const viewportHeight = cardWheelViewportHeight(wheel);
  const focusLine = Math.min(viewportHeight / 2, pitch * 1.55);
  const startPadding = Math.max(13, focusLine - sample.offsetHeight / 2);
  const endPadding = Math.max(
    13,
    viewportHeight - focusLine - sample.offsetHeight / 2,
  );
  wheel.style.height = `${viewportHeight}px`;
  wheel.style.maxHeight = `${viewportHeight}px`;
  wheel.style.setProperty("--wheel-start-padding", `${startPadding}px`);
  wheel.style.setProperty("--wheel-end-padding", `${endPadding}px`);
}

function centreWheelChild(wheel: HTMLElement, child: HTMLElement, behavior: ScrollBehavior) {
  prepareCardWheel(wheel);
  const children = Array.from(wheel.children) as HTMLElement[];
  const second = children[1];
  const pitch = Math.max(
    1,
    second ? second.offsetTop - children[0].offsetTop : child.offsetHeight,
  );
  const viewportHeight = cardWheelViewportHeight(wheel);
  const focusLine = Math.min(viewportHeight / 2, pitch * 1.55);
  wheel.scrollTo({
    top: Math.max(0, child.offsetTop + child.offsetHeight / 2 - focusLine),
    behavior,
  });
}

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
  const [compactLayout, setCompactLayout] = useState(false);
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
    const query = window.matchMedia("(max-width: 900px)");
    const update = () => setCompactLayout(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const wheel = cardWheelRef.current;
    if (!wheel) return;
    if (!compactLayout) {
      wheel.style.removeProperty("height");
      wheel.style.removeProperty("max-height");
      wheel.style.removeProperty("--wheel-start-padding");
      wheel.style.removeProperty("--wheel-end-padding");
      return;
    }
    const initialIndex = filteredItems.length > 1 ? 1 : 0;
    const target = wheel.children[initialIndex] as HTMLElement | undefined;
    if (!target) return;
    setActiveCard(initialIndex);
    const frame = window.requestAnimationFrame(() => {
      centreWheelChild(wheel, target, "auto");
      updateCardWheelGeometry(wheel);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [compactLayout, filteredItems]);

  useEffect(() => () => {
    if (cardScrollFrame.current !== null) window.cancelAnimationFrame(cardScrollFrame.current);
  }, []);

  useEffect(() => {
    const wheel = cardWheelRef.current;
    if (!wheel || !compactLayout) return;
    const update = () => {
      prepareCardWheel(wheel);
      updateCardWheelGeometry(wheel);
    };
    const frame = window.requestAnimationFrame(update);
    const observer = new ResizeObserver(update);
    observer.observe(wheel);
    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [activeCard, compactLayout, filteredItems]);

  function handleCardWheelScroll(event: UIEvent<HTMLElement>) {
    const wheel = event.currentTarget;
    if (cardScrollFrame.current !== null) window.cancelAnimationFrame(cardScrollFrame.current);
    cardScrollFrame.current = window.requestAnimationFrame(() => {
      const index = updateCardWheelGeometry(wheel);
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
              <Link
                key={item.key}
                href={item.href}
                className="region-card-stack__spacer"
                aria-label={`Open ${item.title} ${folderType.label.toLowerCase()} folder`}
                onFocus={(event) => {
                  const wheel = cardWheelRef.current;
                  if (wheel) centreWheelChild(wheel, event.currentTarget, "smooth");
                  setActiveCard(index);
                }}
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
        <summary aria-label={`Open filters for ${folderType.label.toLowerCase()} folders. ${isolatedReviewCount} review routes remain outside the active stack.`}>
          <span className="folder-filter-disc" aria-hidden="true" />
          <span className="label-caps">Filter</span>
          <strong>{filteredItems.length}</strong>
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
        </div>
      </details>
    </div>
  );
}
