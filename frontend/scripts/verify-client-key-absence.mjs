import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const envPath = join(frontend, ".env.local");
let key = "";
try {
  for (const line of readFileSync(envPath, "utf8").split(/\r?\n/)) {
    if (line.startsWith("DEEPSEEK_API_KEY=")) key = line.slice("DEEPSEEK_API_KEY=".length);
  }
} catch {
  console.log("CLIENT_KEY_BUNDLE_SCAN=PASS NO_LOCAL_KEY_PRESENT=true");
  process.exit(0);
}
if (!key) {
  console.log("CLIENT_KEY_BUNDLE_SCAN=PASS LOCAL_KEY_EMPTY=true");
  process.exit(0);
}
if (key.length < 12) throw new Error("DEEPSEEK_API_KEY is too short to perform a meaningful bundle scan");
const staticRoot = join(frontend, ".next", "static");
const matches = [];
function scan(directory) {
  for (const name of readdirSync(directory)) {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) scan(path);
    else if (readFileSync(path).includes(Buffer.from(key))) matches.push(path.slice(frontend.length + 1));
  }
}
scan(staticRoot);
key = "";
if (matches.length) throw new Error(`CLIENT_KEY_BUNDLE_SCAN=FAIL MATCH_COUNT=${matches.length}`);
console.log("CLIENT_KEY_BUNDLE_SCAN=PASS MATCH_COUNT=0");
