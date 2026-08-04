import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import {
  TRACE_FAMILY_META,
  TRACE_TYPE_BY_ID,
  TRACE_TYPE_DEFINITIONS,
} from "@/components/archive/trace/trace-taxonomy";
import styles from "./TraceTypePage.module.css";

type PageProps = { params: Promise<{ type: string }> };

export function generateStaticParams() {
  return TRACE_TYPE_DEFINITIONS.map((definition) => ({ type: definition.id }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { type } = await params;
  const definition = TRACE_TYPE_BY_ID.get(type);
  if (!definition) return { title: "TRACE type not found" };
  return {
    title: `${definition.code} — TRACE relation type`,
    description: definition.definition,
  };
}

export default async function TraceTypePage({ params }: PageProps) {
  const { type } = await params;
  const definition = TRACE_TYPE_BY_ID.get(type);
  if (!definition) notFound();
  const family = TRACE_FAMILY_META[definition.family];
  const peers = TRACE_TYPE_DEFINITIONS.filter((item) => item.family === definition.family);

  return (
    <ArchiveShell
      activeNav="trace"
      mainScroll
      main={(
        <main className={styles.page}>
          <nav className={styles.breadcrumb} aria-label="Breadcrumb">
            <Link href="/trace">TRACE</Link><span>/</span><span>Relation types</span><span>/</span><b>{definition.code}</b>
          </nav>

          <header className={styles.header}>
            <div>
              <p>{family.code} / {family.label}</p>
              <h1>{definition.label}</h1>
            </div>
            <dl>
              <div><dt>Type code</dt><dd>{definition.code}</dd></div>
              <div><dt>Frozen v48 edges</dt><dd>{definition.count.toLocaleString()}</dd></div>
              <div><dt>Status</dt><dd>{definition.status.replaceAll("_", " ")}</dd></div>
            </dl>
          </header>

          <section className={styles.statement}>
            <p className={styles.kicker}>Normalized definition</p>
            <p>{definition.definition}</p>
          </section>

          <section className={styles.rules} aria-label="TRACE assertion rules">
            <article>
              <p>Evidence required</p>
              <h2>{definition.evidenceRequirement}</h2>
            </article>
            <article>
              <p>Permitted assertion</p>
              <h2>{definition.allowedAssertion}</h2>
            </article>
            <article data-warning="true">
              <p>Prohibited inference</p>
              <h2>{definition.prohibitedInference}</h2>
            </article>
          </section>

          <section className={styles.familySection}>
            <div>
              <p>Family question</p>
              <h2>{family.question}</h2>
            </div>
            <div>
              <p>Boundary</p>
              <h2>Relation-type codes normalize display and analysis only. They do not rewrite frozen edge IDs or upgrade analytical associations into historical influence.</h2>
            </div>
          </section>

          <section className={styles.peerTypes} aria-labelledby="peer-types-title">
            <header>
              <p>Same family</p>
              <h2 id="peer-types-title">{family.label} vocabulary</h2>
            </header>
            <table>
              <thead><tr><th>Code</th><th>Type</th><th>v48 edges</th><th>Status</th></tr></thead>
              <tbody>
                {peers.map((item) => (
                  <tr key={item.id} data-current={item.id === definition.id}>
                    <td><Link href={`/trace/types/${item.id}`}>{item.code}</Link></td>
                    <td>{item.label}</td>
                    <td>{item.count.toLocaleString()}</td>
                    <td>{item.status.replaceAll("_", " ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </main>
      )}
    />
  );
}
