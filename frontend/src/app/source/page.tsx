import type { Metadata } from "next";
import SourceView from "./SourceView";

export const metadata: Metadata = {
  title: "Source",
  description:
    "Provenance, acquisition status, rights conditions, transformation record, evidence status, and reproducibility for the materials incorporated into Modern Graphic Design Archive.",
};

export default function SourcePage() {
  return <SourceView />;
}
