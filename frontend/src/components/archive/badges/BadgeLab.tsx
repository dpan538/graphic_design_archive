type BadgeShape =
  | "b01"
  | "b02"
  | "b03"
  | "b04"
  | "b05"
  | "b06"
  | "b07"
  | "b08"
  | "b09"
  | "b10"
  | "b11"
  | "b12"
  | "b13"
  | "b14"
  | "b15"
  | "b16";

type BadgeTone = "paper" | "ink" | "blue" | "orange" | "green";

interface BadgeAsset {
  code: string;
  label: string;
  note: string;
  detail: string;
  shape: BadgeShape;
  tone: BadgeTone;
  mark: string;
  script?: "latin" | "jp" | "devanagari" | "symbol";
}

interface BadgeGroup {
  code: string;
  title: string;
  description: string;
  assets: BadgeAsset[];
}

const badgeGroups: BadgeGroup[] = [
  {
    code: "B01",
    title: "Archive Control",
    description: "The strongest English control marks: record logic first, silhouette second.",
    assets: [
      { code: "EN01", label: "INDEX", note: "folder order", detail: "chronology / shelf marker", shape: "b01", tone: "paper", mark: "I" },
      { code: "EN02", label: "SOURCE", note: "return path", detail: "external record + citation", shape: "b02", tone: "ink", mark: "S" },
      { code: "EN03", label: "RIGHTS", note: "reuse state", detail: "policy / permission check", shape: "b03", tone: "paper", mark: "R" },
      { code: "EN04", label: "TRACE", note: "provenance", detail: "captured / normalized / reviewed", shape: "b04", tone: "blue", mark: "T" },
      { code: "EN05", label: "FOLDER", note: "membership", detail: "region / theme / medium / movement", shape: "b05", tone: "green", mark: "F" },
      { code: "EN06", label: "IMAGE", note: "visual state", detail: "IMG00-IMG04 display code", shape: "b06", tone: "orange", mark: "IMG" },
      { code: "EN07", label: "CARD", note: "surface unit", detail: "below-sheet record asset", shape: "b07", tone: "paper", mark: "C" },
      { code: "EN08", label: "APPENDIX", note: "overflow table", detail: "p02/p03 continuation mark", shape: "b08", tone: "ink", mark: "A" },
    ],
  },
  {
    code: "B02",
    title: "Global File Marks",
    description: "A tighter cross-script set: Japanese kana, Devanagari, Spanish, and two symbols.",
    assets: [
      { code: "JP01", label: "きろく", note: "record", detail: "surface record file", shape: "b09", tone: "blue", mark: "き", script: "jp" },
      { code: "JP02", label: "さくいん", note: "index", detail: "cross-reference marker", shape: "b10", tone: "paper", mark: "さ", script: "jp" },
      { code: "IN01", label: "अभिलेख", note: "archive", detail: "archive file packet", shape: "b11", tone: "green", mark: "अ", script: "devanagari" },
      { code: "IN02", label: "स्रोत", note: "source", detail: "source return stamp", shape: "b12", tone: "orange", mark: "स्", script: "devanagari" },
      { code: "ES01", label: "ARCHIVO", note: "file", detail: "special file mark", shape: "b13", tone: "blue", mark: "A" },
      { code: "ES02", label: "FUENTE", note: "source", detail: "source return label", shape: "b14", tone: "paper", mark: "F" },
      { code: "SY01", label: "※", note: "annotation", detail: "editorial note symbol", shape: "b15", tone: "paper", mark: "※", script: "symbol" },
      { code: "SY02", label: "§", note: "protocol", detail: "rule / policy symbol", shape: "b16", tone: "ink", mark: "§", script: "symbol" },
    ],
  },
];

function BadgeAssetView({ asset }: { asset: BadgeAsset }) {
  return (
    <article
      className="archive-symbol-badge"
      data-shape={asset.shape}
      data-tone={asset.tone}
      data-script={asset.script ?? "latin"}
    >
      <span className="archive-symbol-badge__shape" aria-hidden />
      <span className="archive-symbol-badge__frame" aria-hidden />
      <span className="archive-symbol-badge__pin" aria-hidden />
      <span className="archive-symbol-badge__code">{asset.code}</span>
      <span className="archive-symbol-badge__mark" aria-hidden>
        {asset.mark}
      </span>
      <strong>{asset.label}</strong>
      <small>{asset.note}</small>
      <em>{asset.detail}</em>
    </article>
  );
}

export default function BadgeLab() {
  return (
    <main className="badge-lab">
      <header className="badge-lab__header">
        <p>Digital asset study / badge set 01</p>
        <h1>Archive Badges</h1>
        <dl>
          <div>
            <dt>groups</dt>
            <dd>2</dd>
          </div>
          <div>
            <dt>assets</dt>
            <dd>16</dd>
          </div>
          <div>
            <dt>mode</dt>
            <dd>symbolic file marks</dd>
          </div>
        </dl>
      </header>
      <div className="badge-lab__groups">
        {badgeGroups.map((group) => (
          <section key={group.code} className="badge-lab__group" data-group={group.code} aria-label={group.title}>
            <header>
              <span>{group.code}</span>
              <h2>{group.title}</h2>
              <p>{group.description}</p>
            </header>
            <div className="badge-lab__grid">
              {group.assets.map((asset) => (
                <BadgeAssetView key={asset.code} asset={asset} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </main>
  );
}
