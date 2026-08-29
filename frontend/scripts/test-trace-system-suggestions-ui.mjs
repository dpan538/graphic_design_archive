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
for (const [name, source] of [["TRACE", tracePage], ["Context", contextPage], ["Spacetime", spacetimePage]]) {
  check(source.indexOf("isLikelyMobileTraceRequest") < source.indexOf("await Promise.all"), `${name} route must return its mobile boundary before loading governed runtime data`);
}
check(mobile.includes("requires a desktop viewport") && mobile.includes('href="/search"'), "direct mobile TRACE must return a lightweight desktop-required route to Search");
check(!/features\/trace|lib\/trace|generated\/trace|public\/data\/trace/.test(read("../src/features/search-v2/ui/SearchWorkspace.tsx")), "mobile Search client must remain free of TRACE imports");

console.log(`TRACE System Suggestions UI contract: ${checks} checks passed`);
