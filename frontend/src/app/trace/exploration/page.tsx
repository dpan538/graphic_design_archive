import type { Metadata } from "next";
import Link from "next/link";
import SiteNav from "@/components/site/SiteNav";
import SiteNavMobile from "@/components/site/mobile/SiteNavMobile";
import { isLikelyMobileTraceRequest, TraceDesktopRequired } from "@/features/trace-v49/mobile.server";
import { FAILURE_BACK, FAILURE_KICKER, FAILURE_NOTE, FAILURE_TITLE, NAME, STATEMENT } from "./lib/content";
import styles from "./page.module.css";

/* /trace/exploration — TRACE's Exploration (FRONTEND_DESIGN_DECISION.md §7i):
   a bounded generative visual explorer over the frozen Exploration V2
   state machine. Server route: the mobile guard first (the desktop-required
   notice before any research runtime is imported); then the view service —
   the starting points, the requested or default view (restored from
   ?map=&state=&template=&variant= when given), the Open Inquiry registry —
   handed to the desktop tree. V3 is never read. A failed build mounts
   nothing but the failure page. */

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Exploration — TRACE",
  description: `${NAME}: ${STATEMENT}`,
  robots: { index: false, follow: false },
};

interface ExplorationPageProps {
  readonly searchParams: Promise<Readonly<Record<string, string | readonly string[] | undefined>>>;
}

const one = (value: string | readonly string[] | undefined): string | undefined => (typeof value === "string" && value.length > 0 && value.length <= 120 ? value : undefined);

/* the landing picture: the modular grid, the treatment the owner chose for the first view */
const LANDING_TEMPLATE = "GRID";

export default async function ExplorationPage({ searchParams }: ExplorationPageProps) {
  if (await isLikelyMobileTraceRequest()) {
    return (
      <>
        <SiteNavMobile />
        <TraceDesktopRequired functionName={NAME} />
      </>
    );
  }
  const params = await searchParams;
  const [{ default: ExplorationDesktop }, view, inquiry] = await Promise.all([
    import("./desktop/ExplorationDesktop"),
    import("@/features/trace-v49/exploration-view/service.server"),
    import("@/features/trace-v49/open-inquiry-v1/service.server"),
  ]);
  try {
    const points = view.listExplorationStartingPoints();
    const inquiries = inquiry.listOpenInquiries();
    if (!points.ok || !inquiries.ok) return <Failure />;
    const map = one(params.map);
    const state = one(params.state);
    const template = one(params.template);
    const variant = one(params.variant);
    const start = one(params.start);
    /* the bare landing opens on the default word drawn as the modular grid (the owner's picture);
       a restored URL or a named start keeps its own presentation */
    const landing = { vocabulary_id: view.getDefaultStartingPointId(), template_id: LANDING_TEMPLATE, variant_id: 0 };
    let initial = map
      ? view.retrieveExplorationView(map, state, template, variant === undefined ? undefined : Number(variant))
      : start
        ? view.createExplorationView({ vocabulary_id: points.data.starting_points.find((point) => point.label === start)?.vocabulary_id ?? view.getDefaultStartingPointId() })
        : view.createExplorationView(landing);
    if (!initial.ok && map) initial = view.createExplorationView(landing);
    if (!initial.ok) return <Failure />;
    return (
      <ExplorationDesktop
        initialView={initial.data}
        startingPoints={points.data.starting_points}
        inquiries={inquiries.data.data.items.map((item) => ({
          inquiryId: item.inquiry_id,
          participants: item.participants.map((participant) => participant.label),
          boundedScope: item.bounded_scope,
          relationForm: item.relation_form,
          governed: item.inquiry_only_association_identity !== null,
        }))}
      />
    );
  } catch {
    return <Failure />;
  }
}

function Failure() {
  return (
    <>
      <SiteNav active="trace" />
      <main id="main" className={styles.failure}>
        <p className={styles.eyebrow}>{FAILURE_KICKER}</p>
        <h1 className={styles.title}>{FAILURE_TITLE}</h1>
        <p className={styles.note}>{FAILURE_NOTE}</p>
        <p className={styles.back}><Link href="/trace">{FAILURE_BACK}</Link></p>
      </main>
    </>
  );
}
