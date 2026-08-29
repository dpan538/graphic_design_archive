import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import Link from "next/link";
import { publicSearchFacets } from "@/features/search-v2/service.server";
import styles from "./HomePage.module.css";

function starterHref(starter: ReturnType<typeof publicSearchFacets>["starterQueries"][number]): string {
  const parameters = new URLSearchParams();
  if (starter.query) parameters.set("q", starter.query);
  for (const [key, value] of Object.entries(starter.filters)) parameters.set(key, String(value));
  return `/search?${parameters.toString()}`;
}

function HomeArchiveBox({ publicCount }: { publicCount: number }) {
  return (
    <details className="home-archive-summary">
      <summary>
        <span>Public objects</span>
        <strong>{publicCount.toLocaleString("en-US")}</strong>
        <small>searchable object pages</small>
      </summary>
      <dl>
        <div>
          <dt>Search scope</dt>
          <dd>{publicCount.toLocaleString("en-US")}</dd>
        </div>
        <div>
          <dt>held included</dt>
          <dd>0</dd>
        </div>
      </dl>
    </details>
  );
}

export default function HomePage() {
  const facets = publicSearchFacets();

  return (
    <ArchiveShell
      mainScroll
      main={(
        <main className={styles.main}>
          <header className={styles.intro}>
            <p className={styles.eyebrow}>Graphic Design Archive</p>
            <h1>Find an object or enter a research space.</h1>
            <p>Global Search and TRACE are parallel ways into the archive. Search opens public object pages; TRACE supports desktop research workflows.</p>
          </header>

          <div className={styles.strategies}>
            <section className={`${styles.card} ${styles.searchCard}`} aria-labelledby="home-search-title">
              <p className={styles.availability}>Desktop and mobile · public objects</p>
              <h2 id="home-search-title">Global Search</h2>
              <p>Search {facets.documentCount.toLocaleString("en-US")} public objects by ID, title, credited name, or place, then refine by year, type, theme, or movement.</p>
              <form className={styles.form} action="/search" method="get" role="search">
                <label className="sr-only" htmlFor="home-search-query">Search public archive objects</label>
                <input id="home-search-query" name="q" type="search" maxLength={160} autoComplete="off" placeholder="Object ID, title, credited name, or place" />
                <button type="submit">Search</button>
              </form>
              <ul className={styles.starters} aria-label="Curated Search starters">
                {facets.starterQueries.map((starter) => <li key={starter.id}><Link href={starterHref(starter)}>{starter.label}</Link></li>)}
              </ul>
              <Link className={styles.routeLink} href="/search">Open the complete Search workspace →</Link>
            </section>

            <section className={styles.card} aria-labelledby="home-trace-title">
              <p className={styles.availability}>Desktop research environment</p>
              <h2 id="home-trace-title">TRACE</h2>
              <p>Explore public research context, spacetime, validated associations, and clearly separated open inquiry.</p>
              <Link className={styles.routeLink} href="/trace">Enter TRACE →</Link>
            </section>
          </div>

          <nav className={styles.browse} aria-label="Other archive routes">
            <span>Browse the archive structure:</span>
            <Link href="/folders">Folders</Link>
            <Link href="/index">Index</Link>
            <Link href="/about">About</Link>
          </nav>
        </main>
      )}
      cornerCard={<HomeArchiveBox publicCount={facets.documentCount} />}
    />
  );
}
