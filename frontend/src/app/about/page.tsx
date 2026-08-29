import type { Metadata } from "next";
import AboutView from "./AboutView";

export const metadata: Metadata = {
  title: "About & Methodology",
  description:
    "Project identity, archive and design research methodology, visual-design references, claim boundaries, and how to cite the Modern Graphic Design Archive.",
};

export default function AboutPage() {
  return <AboutView />;
}
