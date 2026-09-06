import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const panel = read("../src/features/system-suggestions/ui/SystemSuggestionsPanel.tsx");
const context = read("../src/features/trace-v49/context/canvas/ContextCanvas.tsx");
const spacetime = read("../src/features/trace-v49/spacetime/map/SpacetimeWorkspace.tsx");
const exploration = read("../src/features/trace-v49/exploration-ui/TraceExplorationReference.tsx");
const tracePage = read("../src/app/trace/page.tsx");
const contextPage = read("../src/app/trace/context-canvas/page.tsx");
const spacetimePage = read("../src/app/trace/spacetime/page.tsx");
const explorationPage = read("../src/app/trace/exploration/page.tsx");
const mobile = read("../src/features/trace-v49/mobile.server.tsx");
let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks += 1; };

check(context.includes('surface="TRACE_CONTEXT"'), "Context Canvas must use the shared TRACE_CONTEXT surface");
check(spacetime.includes('surface="TRACE_SPACETIME"'), "Spacetime must use the shared TRACE_SPACETIME surface");
check(exploration.includes('surface="TRACE_VALIDATED_EXPLORATION"'), "Exploration must use the validated guidance surface");
check(exploration.includes('surface="TRACE_OPEN_INQUIRY"'), "Exploration must use the separate Open Inquiry guidance surface");
check(panel.includes('fetch("/api/system-suggestions/v1"'), "all TRACE guidance must use the shared endpoint");
check(panel.includes("Evidence remains incomplete.") && panel.includes("This is not a validated historical association."), "Open Inquiry must hard-code both mandatory evidence sentences");
check(panel.indexOf("data-open-inquiry-disclosure") < panel.indexOf("{response ?"), "fixed Open Inquiry disclosure must render before optional guidance");
check(panel.includes("System suggests") && !/DeepSeek|Powered by AI|Ask AI|AI suggests|model-generated/.test(`${panel}\n${context}\n${spacetime}\n${exploration}`), "TRACE surfaces must use only the public guidance label");
check(!/response\.(?:sourceClass|providerStatus)|body\.(?:sourceClass|providerStatus)/.test(panel), "TRACE UI must not display provider source class or status");
check(panel.includes("onClick={() => onAction(suggestion)}") && !panel.includes("onAction(suggestion);") , "TRACE actions must require an explicit user click");
check(context.includes('evidenceClass: "PUBLIC_CONTEXT"') && spacetime.includes('evidenceClass: "PUBLIC_AGGREGATE"'), "Context and Spacetime must send their bounded public evidence classes");
check(exploration.includes('evidenceClass: "VALIDATED"') && exploration.includes('evidenceClass: "OPEN_INQUIRY"'), "validated and inquiry summaries must remain evidence-class separated");
check(context.includes("availableEntities.find") && spacetime.includes("atlas.accessibleRows.find"), "suggestion actions must select only currently valid UI candidates");
check(exploration.includes("No validated composition is active in this release."), "zero validated product state must remain explicit");
check(exploration.includes("none may enter validated topology"), "Open Inquiry must not be promoted into validated topology");
/* the mobile boundary stands before any governed runtime load; a route that loads none (the TRACE landing) passes on the guard alone */
for (const [name, source] of [["TRACE", tracePage], ["Context", contextPage], ["Spacetime", spacetimePage], ["Exploration", explorationPage]]) {
  const guard = source.indexOf("isLikelyMobileTraceRequest()");
  const load = source.indexOf("await Promise.all");
  check(load < 0 || (guard >= 0 && guard < load), `${name} route must return its mobile boundary before loading governed runtime data`);
}
/* the release pass (2026-09-06): the live desktop surfaces name their state (v2 references); no client-described facts reach a model */
const description = read("../src/app/trace/exploration/desktop/DescriptionDrawer.tsx");
const inquiryDrawer = read("../src/app/trace/exploration/desktop/InquiryDrawer.tsx");
const contextDesktop = read("../src/app/trace/context-canvas/desktop/ContextDesktop.tsx");
const searchWorkspace = read("../src/features/search-v2/ui/SearchWorkspace.tsx");
check(description.includes('surface="TRACE_VALIDATED_EXPLORATION"') && description.includes("reference={reference}") && description.includes("maxActions={0}"), "the Exploration Description names its state and stays narration-only");
check(inquiryDrawer.includes('surface="TRACE_OPEN_INQUIRY"') && inquiryDrawer.includes("reference={reference}") && inquiryDrawer.includes("maxActions={1}"), "the Open Inquiry drawer names its inquiry and offers at most one action");
check(contextDesktop.includes('surface="TRACE_CONTEXT"') && contextDesktop.includes("reference={suggestionReference}") && contextDesktop.includes("maxActions={1}"), "the Context Canvas names its object and canvas and offers at most one action");
check(searchWorkspace.includes('schemaVersion: "gda-system-suggestions-request/v2"') && searchWorkspace.includes("shown: { exactResultCount"), "Search names its query and filters and states the count it shows");
check(/OPEN_INQUIRY_DISCLOSURE\[0\][\s\S]*OPEN_INQUIRY_DISCLOSURE\[1\][\s\S]*OPEN_INQUIRY_DISCLOSURE\[2\]/.test(inquiryDrawer) && read("../src/app/trace/exploration/lib/content.ts").includes('"Open inquiry",\n  "Evidence remains incomplete.",\n  "This is not a validated historical association.",'), "the Open Inquiry disclosure is fixed UI text in its order");
check(description.includes("View association details") || read("../src/app/trace/exploration/lib/content.ts").includes('ASSOCIATION_DETAILS = "View association details"'), "the Description carries the program's association details entry");
check(!/DeepSeek|Powered by AI|Ask AI|AI suggests|model-generated/.test(`${description}\n${inquiryDrawer}\n${contextDesktop}\n${searchWorkspace}`), "the live surfaces use only the public guidance label");
check(!/response\.(?:sourceClass|providerStatus|contextFingerprint)|guidance\.(?:sourceClass|providerStatus)/.test(`${panel}\n${searchWorkspace}`), "no surface displays a provider class, status or fingerprint");
check(mobile.includes("requires a desktop viewport") && mobile.includes('href="/search"'), "direct mobile TRACE must return a lightweight desktop-required route to Search");
check(!/features\/trace|lib\/trace|generated\/trace|public\/data\/trace/.test(read("../src/features/search-v2/ui/SearchWorkspace.tsx")), "mobile Search client must remain free of TRACE imports");

console.log(`TRACE System Suggestions UI contract: ${checks} checks passed`);
