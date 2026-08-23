import type { Metadata } from "next";
import ContextCanvas from "@/features/trace-v49/context/canvas/ContextCanvas";

export const metadata: Metadata = {
  title: "Context Canvas functional prototype — TRACE v49",
  description: "Unlinked, synthetic-data-only functional prototype for the TRACE Context Canvas.",
  robots: {
    index: false,
    follow: false,
  },
};

export default function ContextCanvasPrototypePage() {
  return <ContextCanvas />;
}
