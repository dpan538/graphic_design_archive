import type { MetadataRoute } from "next";
export default function robots(): MetadataRoute.Robots {
  const disallow = ["/api/", "/search", "/trace/", "/data/", "/contents", "/folders", "/main-sheets", "/sub-sheets", "/text-pages", "/cards", "/bookmarks", "/badges", "/slips", "/appendix", "/reading-notes"];
  return { rules: [{ userAgent: ["*", "OAI-SearchBot"], allow: "/", disallow }, { userAgent: ["GPTBot", "Google-Extended", "CCBot"], disallow: "/" }], sitemap: "https://mgdarchive.com/sitemap.xml" };
}
