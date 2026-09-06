import { aboutMarkdown } from "@/features/machine-reading/markdown";
export const dynamic = "force-static";
export function GET() { return new Response(aboutMarkdown, { headers: { "Content-Type": "text/markdown; charset=utf-8", "X-Content-Type-Options": "nosniff", Link: '<https://mgdarchive.com/about>; rel="canonical"' } }); }
