import eligibility from "../../../generated/reader-eligibility-v49/manifest.json";
export const site = "https://mgdarchive.com";
export const repository = "https://github.com/dpan538/graphic_design_archive";
export const implementation = [
  { title: "Project and contribution", text: "Modern Graphic Design Archive is a rights-aware reading and research interface, not a complete history of graphic design. Dai Pan leads the project’s research, data governance, design and implementation, with AI-assisted development and verification." },
  { title: "Current capabilities", text: "Index, Search and Object records support public reading. Context Canvas and Exploration distinguish recorded context, validated associations and open inquiries. Spacetime is not released." },
  { title: "Implementation", text: "The application uses Next.js, React and TypeScript with generated, versioned server read models. PostgreSQL and Python support research and data preparation; public page reads do not require a live research database. Redis provides shared fixed-window request limits. Optional DeepSeek suggestions pass fact validation and have deterministic fallbacks; ordinary project and metadata reading does not call the model." },
  { title: "Publication boundaries", text: `${eligibility.counts.public.toLocaleString("en-US")} public records include ${eligibility.counts.index_eligible.toLocaleString("en-US")} reader-facing objects and ${eligibility.counts.record_only.toLocaleString("en-US")} record-only entries. Normal Search and Index browse reader-facing objects; exact identifier Search can retrieve public record-only entries. Held material is not a public reading resource. Metadata publication does not grant image reuse or training rights.` },
  { title: "Verification and release", text: "Local desktop and mobile acceptance and real provider tests have been performed. Automated checks cover data contracts, eligibility, fact boundaries and failure handling; assertion counts are not counts of user scenarios. Vercel integration is being prepared; remote production acceptance has not been completed. Source describes provenance and reproducibility." },
];
export function safeJsonLd(value: unknown) {
  return JSON.stringify(value).replace(/</g, "\\u003c").replace(/>/g, "\\u003e").replace(/&/g, "\\u0026").replace(/\u2028/g, "\\u2028").replace(/\u2029/g, "\\u2029");
}
export const projectJsonLd = { "@context": "https://schema.org", "@graph": [
  { "@type": "WebSite", "@id": `${site}/#website`, name: "Modern Graphic Design Archive", url: site, description: implementation[0].text },
  { "@type": "SoftwareSourceCode", name: "MGDA web application", codeRepository: repository, programmingLanguage: ["TypeScript", "Python", "SQL"], author: { "@type": "Person", name: "Dai Pan", url: "https://daipan.art" } },
] };
