import { sourceMarkdown } from "@/features/machine-reading/markdown";
export const dynamic = "force-static";
export function GET() { return new Response(sourceMarkdown, { headers: { "Content-Type": "text/markdown; charset=utf-8", "X-Content-Type-Options": "nosniff", Link: '<https://mgdarchive.com/source>; rel="canonical"' } }); }
