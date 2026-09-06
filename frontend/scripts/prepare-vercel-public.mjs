// Only execute in an ephemeral Vercel/CI checkout, never the owner's working tree.
import { existsSync, mkdirSync, readdirSync, renameSync, copyFileSync, readFileSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
const root = process.cwd();
if (process.env.VERCEL !== "1" && process.env.MGDA_EPHEMERAL_BUILD !== "1") throw new Error("Public staging requires an ephemeral build checkout");
if (root.includes("modern_GD_history_frontend_redesign")) throw new Error("Refusing to alter the owner worktree public directory");
const publicDir = join(root, "public"), backup = join(root, ".mgda-private-public");
const allowed = "trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson";
function files(dir, prefix = "") { return readdirSync(dir, {withFileTypes: true}).flatMap(e => e.isSymbolicLink() ? (() => { throw new Error("Public symlink rejected"); })() : e.isDirectory() ? files(join(dir,e.name), prefix+e.name+"/") : [prefix+e.name]); }
if (!existsSync(backup)) {
 const names = files(publicDir).filter(p => p !== ".DS_Store");
 const unknown = names.filter(p => p !== allowed && !p.startsWith("data/"));
 if (unknown.length) throw new Error("Unreviewed public files: " + unknown.join(","));
 if (!existsSync(join(publicDir,allowed))) throw new Error("Required reviewed geography missing");
 renameSync(publicDir,backup); mkdirSync(dirname(join(publicDir,allowed)),{recursive:true});
 copyFileSync(join(backup,allowed),join(publicDir,allowed));
}
const actual = files(publicDir);
if (actual.length !== 1 || actual[0] !== allowed) throw new Error("Public allowlist mismatch");
console.log(JSON.stringify({ publicFiles: actual, frozenOriginalsRetainedInBuildBackup: true }));
