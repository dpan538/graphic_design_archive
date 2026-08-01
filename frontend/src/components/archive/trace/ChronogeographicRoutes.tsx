import styles from "./TraceExplorer.module.css";
import type { AtlasRegion, TraceAtlas } from "./trace-types";

export default function ChronogeographicRoutes({
  atlas,
  exploreCell,
}: {
  atlas: TraceAtlas;
  exploreCell: (row: AtlasRegion, decade: number) => void;
}) {
  const maximum = Math.max(...atlas.regionMatrix.flatMap((row) => row.counts));
  const gridStyle = { ["--trace-decades" as string]: String(atlas.decades.length) };
  return (
    <section className={styles.chronoRoutes} aria-labelledby="chrono-routes-title">
      <header className={styles.chronoHeading}>
        <div>
          <p>TIME AXIS / VERIFIED OBJECT GEOGRAPHY</p>
          <h3 id="chrono-routes-title">Chronogeographic observation routes</h3>
        </div>
        <p>
          Region rails are categorical axes. Only stations denote records; the connecting rail does not assert diffusion, continuity or influence.
        </p>
      </header>

      <div className={styles.chronoDesktop}>
        <div className={styles.chronoAxisRow}>
          <span>Object geography</span>
          <div className={styles.chronoAxis} style={gridStyle} aria-hidden="true">
            {atlas.decades.map((decade) => <span key={decade}>{decade}</span>)}
          </div>
          <span>Total</span>
        </div>
        {atlas.regionMatrix.map((row) => (
          <div className={styles.chronoRow} key={row.region}>
            <strong>{row.region}</strong>
            <div className={styles.chronoRail} style={gridStyle}>
              {row.counts.map((count, index) => (
                <span className={styles.chronoCell} key={atlas.decades[index]}>
                  {count ? (
                    <button
                      type="button"
                      className={styles.chronoStation}
                      style={{
                        ["--station-size" as string]: `${Math.round(
                          11 + (Math.log1p(count) / Math.log1p(maximum)) * 15,
                        )}px`,
                      }}
                      aria-label={`${row.region}, ${atlas.decades[index]}s: ${count} active objects. Open filtered object list.`}
                      onClick={() => exploreCell(row, atlas.decades[index])}
                    >
                      <span className={styles.srOnly}>{count.toLocaleString()}</span>
                    </button>
                  ) : <i aria-hidden="true" />}
                </span>
              ))}
            </div>
            <b>{row.total.toLocaleString()}</b>
          </div>
        ))}
      </div>
      <div className={styles.chronoLegend}>
        <span><i className={styles.legendRail} />Normalized region rail</span>
        <span><i className={styles.legendStation} />Recorded objects; area uses log-scaled count</span>
        <span><i className={styles.legendGap} />No active record in that decade</span>
      </div>
    </section>
  );
}
