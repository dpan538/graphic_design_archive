import { implementation, site, repository } from "@/features/machine-reading/project";
export const dynamic = "force-static";
export function GET() { return new Response([
  "# Modern Graphic Design Archive", `> ${implementation[0].text}`, implementation[1].text, implementation[3].text,
  "## Selected reading", ...[["About and implementation", "/about.md"], ["Sources and rights", "/source.md"], ["Index", "/directory"], ["Public reading API", "/read-api"]].map(([name,path]) => `- [${name}](${site}${path})`), `- [Repository](${repository})`,
  "Search discovery does not grant training or image reuse permission. Interactive suggestions and export generation are not machine-reading entry points.",
].join("\n\n") + "\n", { headers: { "Content-Type": "text/plain; charset=utf-8" } }); }
