import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const home = read("../src/app/page.tsx");
const page = read("../src/app/search/page.tsx");
const workspace = read("../src/features/search-v2/ui/SearchWorkspace.tsx");
const shellSearch = read("../src/components/archive/shell/search.tsx");
const URL_FIELDS = ["q", "yearFrom", "yearTo", "objectType", "theme", "movement"];
let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks += 1; };

check(home.indexOf("Global Search") < home.indexOf(">TRACE<"), "Global Search must precede TRACE on the homepage");
check(home.includes('action="/search"') && home.includes('method="get"'), "homepage must submit to canonical Search URL");
check(home.includes("facets.starterQueries.map"), "homepage starters must come from the public facet artifact");
check(!/traceAtlas|trace-v48|features\/trace|lib\/trace/.test(home), "homepage must not import a TRACE runtime or read model");
check(page.includes("@/features/search-v2/ui/SearchWorkspace"), "Search page must use the v2 public object workspace");
check(workspace.includes("/api/search/v1?"), "Search UI must query the server-side public Search endpoint");
check(URL_FIELDS.every((field) => workspace.includes(`\"${field}\"`)), "Search UI must preserve text and all four filter families in URL state");
check(workspace.includes('next.set("after", cursor)'), "Search UI must expose bounded cursor pagination in URL state");
check(workspace.includes("router.back()") && workspace.includes("Retry"), "Search UI must support back navigation and retry");
check(workspace.includes("Not recorded") && workspace.includes("No public objects match"), "Search UI must show partial-data and zero-result states");
check(workspace.includes("result.objectPageRoute"), "Search results must link to canonical object pages");
check(!/audit\.score|explanation\.score|raw score/i.test(workspace), "normal Search UI must not expose numeric audit scores");
check(!/DeepSeek|Powered by AI|Ask AI|AI suggests|model-generated/.test(`${home}\n${workspace}\n${shellSearch}`), "public Search surfaces must not expose provider or AI labels");
check(workspace.includes("System suggests") && workspace.includes("/api/system-suggestions/v1"), "Search results must request optional guidance under the shared public label");
check(!/guidance\.(?:sourceClass|providerStatus)|body\.(?:sourceClass|providerStatus)/.test(workspace), "normal Search UI must not display source class or provider status");
check(!/features\/trace|lib\/trace|generated\/trace|public\/data\/trace/.test(`${page}\n${workspace}`), "Search client boundary must not import TRACE code or data");

console.log(`Search v2 UI contract: ${checks} checks passed`);
