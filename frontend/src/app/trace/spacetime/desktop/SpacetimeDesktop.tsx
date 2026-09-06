"use client";

import { useCallback, useEffect, useState } from "react";
import SiteNav from "@/components/site/SiteNav";
import type { SpacetimeRendererMode } from "@/features/trace-v49/spacetime/gis";
import type { PublicSpacetimeAtlasDataset, PublicSpacetimePeriodsDataset } from "@/features/trace-v49/spacetime/governed/types";
import { useSpacetimeWorkspace, type SpacetimeLayer } from "@/features/trace-v49/spacetime/map";
import Dock, { PanelGlyph, TableGlyph } from "../../_shared/Dock";
import {
  DOCK_TOOLS,
  LAYERS,
  PLACE_PROFILE_CLOSE,
  PLACE_PROFILE_DISABLED,
  PLACE_PROFILE_OPEN,
  RANKING_CLOSE,
  RANKING_OPEN,
  STATUS_LAYER,
  STATUS_PERIOD,
  STATUS_RESET,
  STATUS_SELECTED,
  STATUS_VIEW,
  VIEWS,
} from "../lib/content";
import type { YearCount } from "../lib/years.server";
import Drawer, { type DrawerTab } from "./Drawer";
import MapFrame from "./MapFrame";
import MatchingRecords from "./MatchingRecords";
import PeriodRail from "./PeriodRail";
import PlaceProfile from "./PlaceProfile";
import PlaceRanking from "./PlaceRanking";
import SpacetimeRail from "./SpacetimeRail";
import styles from "./SpacetimeDesktop.module.css";

/* Spacetime, desktop (§7h): the presentation over the workspace's one
   orchestration (useSpacetimeWorkspace — the period, the atlas and its
   two neighbours, the geometry, the selection, the record pages, the
   temporal window, the ranking, the guidance context; the GIS as
   sealed). Under the nav: the rail (the period profile, the layer, the
   style), the map column — the period rail above the map, one drawer
   under it (the matching records or the place ranking, never both) —
   and PLACE PROFILE beside the map once a place is chosen, the map
   reflowing beside it. Nothing chosen: no panel, the dock's control
   disabled and saying why. The page does not scroll. */

export interface SpacetimeDesktopProps {
  readonly periods: PublicSpacetimePeriodsDataset;
  readonly initialAtlas: PublicSpacetimeAtlasDataset;
  readonly years: readonly YearCount[];
}

export default function SpacetimeDesktop({ periods, initialAtlas, years }: SpacetimeDesktopProps) {
  const [drawer, setDrawer] = useState<DrawerTab | null>(null);
  const [panelClosed, setPanelClosed] = useState(false);
  const [note, setNote] = useState<string>(STATUS_PERIOD(initialAtlas.selectedPeriod.label));
  const openDrawer = useCallback((tab: DrawerTab) => {
    setDrawer(tab);
    window.requestAnimationFrame(() => {
      document.getElementById("spacetime-drawer")?.focus({ preventScroll: true });
    });
  }, []);
  const workspace = useSpacetimeWorkspace(periods, initialAtlas, { onCompareCounts: () => openDrawer("table") });
  const {
    atlas,
    atlasState,
    failedPeriodId,
    layer,
    setLayer,
    adjacent,
    temporal,
    ranking,
    profile,
    selectedSeries,
    selectedDensity,
    geometry,
    geometryState,
    mode,
    setMode,
    viewBox,
    fullViewBox,
    selectedPeriodId,
    selectedGeographyId,
    selectedGeography,
    selectedDetail,
    marks,
    records,
    recordPage,
    recordsState,
    selectPeriod,
    retryPeriod,
    selectGeography,
    resetMap,
    loadRecordPage,
    loadMore,
    suggestionContext,
    applySuggestion,
  } = workspace;

  const loadingPeriodLabel = periods.periods.find((period) => period.periodId === selectedPeriodId)?.label ?? null;

  const choosePeriod = useCallback((periodId: string) => {
    selectPeriod(periodId);
    setDrawer((current) => (current === "records" ? null : current));
    const label = periods.periods.find((period) => period.periodId === periodId)?.label;
    if (label) setNote(STATUS_PERIOD(label));
  }, [periods.periods, selectPeriod]);

  const chooseGeography = useCallback((geographyId: string) => {
    selectGeography(geographyId);
    setPanelClosed(false);
    const row = atlas.accessibleRows.find((candidate) => candidate.geographyId === geographyId);
    if (row) setNote(STATUS_SELECTED(row.label));
  }, [atlas.accessibleRows, selectGeography]);

  /* WORLD VIEW: the selection cleared, the whole period on the map —
     the period, the layer and the style stay as they are */
  const worldView = useCallback(() => {
    resetMap();
    setDrawer((current) => (current === "records" ? null : current));
    setNote(STATUS_RESET);
  }, [resetMap]);

  const chooseMode = useCallback((next: SpacetimeRendererMode) => {
    setMode(next);
    setNote(STATUS_VIEW(VIEWS.find((view) => view.id === next)?.label ?? next));
  }, [setMode]);

  const chooseLayer = useCallback((next: SpacetimeLayer) => {
    setLayer(next);
    setNote(STATUS_LAYER(LAYERS.find((item) => item.id === next)?.label ?? next));
  }, [setLayer]);

  useEffect(() => {
    if (!selectedGeographyId) setPanelClosed(false);
  }, [selectedGeographyId]);

  const panelOpen = Boolean(selectedGeography) && !panelClosed;
  const guidanceReady = Boolean(selectedGeography) && atlasState === "ready" && adjacent.state !== "loading" && geometryState !== "loading" && recordsState !== "error" && failedPeriodId === null;
  const periodEntry = periods.periods.find((period) => period.periodId === atlas.selectedPeriod.periodId) ?? atlas.selectedPeriod;
  const rankingOpen = drawer === "table";
  const notPlotted = ranking.filter(({ row }) => row.mappingState !== "mapped");

  return (
    <div className={styles.page}>
      <a href="#main" className="skip-link">Skip to content</a>
      <SiteNav active="trace" revealTone="light" />
      <Dock
        active="spacetime"
        toolsLabel={DOCK_TOOLS}
        tools={[
          {
            id: "place-profile",
            revealOpen: PLACE_PROFILE_CLOSE,
            revealClosed: selectedGeography ? PLACE_PROFILE_OPEN : PLACE_PROFILE_DISABLED,
            open: panelOpen,
            disabled: !selectedGeography,
            controls: "spacetime-place-profile",
            onClick: () => setPanelClosed((current) => !current),
            glyph: <PanelGlyph open={panelOpen} />,
          },
          {
            id: "place-ranking",
            revealOpen: RANKING_CLOSE,
            revealClosed: RANKING_OPEN,
            open: rankingOpen,
            controls: "spacetime-drawer",
            onClick: () => (rankingOpen ? setDrawer(null) : openDrawer("table")),
            glyph: <TableGlyph open={rankingOpen} />,
          },
        ]}
      />
      <main id="main" className={styles.main} data-panel={panelOpen ? "open" : "closed"}>
        <div className={styles.rail}>
          <SpacetimeRail
            period={periodEntry}
            profile={profile}
            layer={layer}
            mode={mode}
            rankingOpen={rankingOpen}
            onLayer={chooseLayer}
            onMode={chooseMode}
            onRanking={() => (rankingOpen ? setDrawer(null) : openDrawer("table"))}
          />
        </div>

        <div className={styles.centre}>
          <PeriodRail
            periods={periods.periods}
            years={years}
            selectedPeriodId={selectedPeriodId}
            layer={layer}
            place={selectedSeries}
            busy={atlasState === "loading"}
            onSelect={choosePeriod}
          />
          <MapFrame
            atlas={atlas}
            geometry={geometry}
            geometryState={geometryState}
            atlasState={atlasState}
            loadingPeriodLabel={loadingPeriodLabel}
            marks={marks}
            mode={mode}
            layer={layer}
            viewBox={viewBox}
            fullViewBox={fullViewBox}
            selectedGeographyId={selectedGeographyId}
            selectedDensity={selectedDensity}
            temporal={temporal}
            windowState={adjacent.state}
            notPlotted={notPlotted}
            status={note}
            onSelect={chooseGeography}
            onWorldView={worldView}
            onRetryPeriod={retryPeriod}
          />
          {drawer ? (
            <Drawer
              open={drawer}
              recordsAvailable={Boolean(selectedGeography)}
              recordCount={recordPage?.totalCount ?? null}
              geographyCount={atlas.accessibleRows.length}
              onTab={setDrawer}
              onClose={() => setDrawer(null)}
            >
              {drawer === "records" && selectedGeography ? (
                <MatchingRecords
                  geographyLabel={selectedGeography.label}
                  periodLabel={atlas.selectedPeriod.label}
                  state={recordsState}
                  records={records}
                  page={recordPage}
                  onLoadMore={loadMore}
                  onRetry={() => loadRecordPage()}
                />
              ) : (
                <PlaceRanking
                  rows={ranking}
                  selectedGeographyId={selectedGeographyId}
                  busy={atlasState === "loading"}
                  onSelect={chooseGeography}
                />
              )}
            </Drawer>
          ) : null}
        </div>

        {panelOpen && selectedGeography ? (
          <div className={styles.right}>
            <PlaceProfile
              atlas={atlas}
              row={selectedGeography}
              detail={selectedDetail}
              series={selectedSeries}
              windowState={adjacent.state}
              guidanceReady={guidanceReady}
              suggestionContext={suggestionContext}
              onSuggestion={applySuggestion}
              onViewRecords={() => openDrawer("records")}
              onWorldView={worldView}
            />
          </div>
        ) : null}
      </main>
    </div>
  );
}
