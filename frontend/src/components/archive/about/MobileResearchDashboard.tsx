type DashboardProps = {
  activeObjects: number;
  traceEdges: number;
  activeTrees: number;
  sourceVerified: number;
  metadataSupported: number;
  influenceEdges: number;
  decades: number[];
  decadeTotals: number[];
  relationTypes: { label: string; count: number; family: string }[];
};

function polylinePoints(values: number[]) {
  const width = 320;
  const height = 62;
  const max = Math.max(...values, 1);
  return values
    .map((value, index) => {
      const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width;
      const y = height - (value / max) * (height - 8) - 4;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export default function MobileResearchDashboard({
  activeObjects,
  traceEdges,
  activeTrees,
  sourceVerified,
  metadataSupported,
  influenceEdges,
  decades,
  decadeTotals,
  relationTypes,
}: DashboardProps) {
  const totalEvidence = sourceVerified + metadataSupported;
  const verifiedShare = totalEvidence ? (sourceVerified / totalEvidence) * 100 : 0;
  const topRelations = relationTypes.slice(0, 4);
  const maxRelation = Math.max(...topRelations.map((item) => item.count), 1);

  return (
    <section className="mobile-about-dashboard" aria-labelledby="mobile-dashboard-title">
      <header>
        <p className="label-caps">Research dashboard · v48</p>
        <h1 id="mobile-dashboard-title">Evidence before spectacle.</h1>
        <p>
          A quick view of the archive&apos;s scale, TRACE structure, and explicit
          non-inference boundary.
        </p>
      </header>

      <div className="mobile-about-dashboard__stats" aria-label="Archive summary">
        <div>
          <strong>{activeObjects.toLocaleString("en-US")}</strong>
          <span>active objects</span>
        </div>
        <div>
          <strong>{traceEdges.toLocaleString("en-US")}</strong>
          <span>evidence relations</span>
        </div>
        <div>
          <strong>{activeTrees}</strong>
          <span>research trees</span>
        </div>
      </div>

      <div className="mobile-about-dashboard__timeline">
        <div className="mobile-about-dashboard__heading">
          <span>Chronology density</span>
          <strong>{decades[0]}–{decades[decades.length - 1]}s</strong>
        </div>
        <svg viewBox="0 0 320 70" role="img" aria-label="Archive object density by decade">
          <line x1="0" y1="64" x2="320" y2="64" />
          <polyline points={polylinePoints(decadeTotals)} />
          {decadeTotals.map((value, index) => {
            const x = decadeTotals.length === 1 ? 160 : (index / (decadeTotals.length - 1)) * 320;
            const max = Math.max(...decadeTotals, 1);
            const y = 62 - (value / max) * 52;
            return <circle key={`${decades[index]}-${value}`} cx={x} cy={y} r="2.25" />;
          })}
        </svg>
      </div>

      <div className="mobile-about-dashboard__relations" aria-label="Largest documented relation types">
        <div className="mobile-about-dashboard__heading">
          <span>Documented relation types</span>
          <strong>top {topRelations.length}</strong>
        </div>
        {topRelations.map((relation) => (
          <div key={relation.label} className="mobile-about-dashboard__relation">
            <span>{relation.label.replaceAll("_", " ")}</span>
            <i style={{ ["--share" as string]: `${(relation.count / maxRelation) * 100}%` }} />
            <strong>{relation.count.toLocaleString("en-US")}</strong>
          </div>
        ))}
      </div>

      <div className="mobile-about-dashboard__evidence">
        <div>
          <span>source verified</span>
          <strong>{verifiedShare.toFixed(1)}%</strong>
        </div>
        <div className="mobile-about-dashboard__evidence-bar" aria-hidden="true">
          <i style={{ ["--verified" as string]: `${verifiedShare}%` }} />
        </div>
        <p>
          {sourceVerified.toLocaleString("en-US")} source-verified · {metadataSupported.toLocaleString("en-US")} metadata-supported
        </p>
      </div>

      <footer>
        <strong>{influenceEdges}</strong>
        <span>inferred influence edges</span>
        <p>Association is never displayed as historical influence.</p>
      </footer>
    </section>
  );
}
