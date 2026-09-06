# MGDA Vercel Import contract

This contract supersedes the historical Upstash prerequisite. Import readiness is independent of an as-yet-unfilled runtime configuration; public release still requires working guidance and remote acceptance. No deployment is created by these scripts.

| Import setting | Value |
|---|---|
| Repository | `dpan538/graphic_design_archive` |
| Candidate branch | `codex/vercel-import-ready`; use the reviewed remote SHA in the final handoff |
| Framework | Next.js |
| Root Directory | `frontend` |
| Node.js | `22.x` (lockfile/engines; Linux x64 verification required) |
| Install Command | `npm ci` |
| Build Command | `npm run build:vercel` |
| Output Directory | Leave the Next.js default; do not override with a local directory |
| Production branch | Keep `main` until the candidate is reviewed and merged under the normal PR process |
| Domain | Do not configure `mgdarchive.com` until first deployment acceptance and explicit authorization |

The build uses Webpack and first moves frozen legacy public files to a private build backup, publishes only the explicit allowlist, then scans public/client output. Do not replace this command with `next build`, Turbopack or upload the local private-runtime. Frozen sources remain in Git. Runtime read models and native PNG dependencies are traced into server functions, never copied to public storage.

## Safe first deployment on Hobby

Hobby's Vercel Authentication **Standard Protection does not protect the production domain**, including its active production alias. Do not assume a normal Import → Deploy click produces a private first site.

For a protected first run, the owner can create the project **without deploying** (`vercel project add mgda --scope dpan538s-projects`), configure the card above and Settings → Deployment Protection → Vercel Authentication → Standard Protection, then connect GitHub with production branch `main`. From Deployments → Create Deployment, choose the candidate non-production branch and Preview target. Verify the dialog's target and the actual unauthenticated access boundary before sharing it. Do not generate shareable bypass links. If the account's UI cannot separate project creation/configuration from production deployment, stop before Deploy and use project-only creation; do not activate a paid protection upgrade as a workaround. This is an owner action after Import preparation, not performed by the agent.

Sources: [project-only CLI](https://vercel.com/docs/cli/project), [protection scope](https://vercel.com/docs/deployment-protection). Hobby remains subject to personal/non-commercial use and resource limits.

## Server environment (never NEXT_PUBLIC)

Set each scope separately in Vercel Settings → Environment Variables. Do not paste secrets into Git, reports or shell arguments. Preview and Production may use the same dedicated service but must use different namespaces and separately stored stable identity secrets.

| Name | Preview | Production | Secret |
|---|---|---|---|
| `REDIS_URL` | Actual TLS Redis/Valkey service URI | Actual approved TLS service URI | Yes |
| `SYSTEM_SUGGESTIONS_RATE_LIMIT_NAMESPACE` | `mgda:preview:system-suggestions:v1` | `mgda:production:system-suggestions:v1` | No |
| `SYSTEM_SUGGESTIONS_IDENTITY_SECRET` | Stable random >=32 chars, same on all Preview instances | Stable separate random >=32 chars, same on all Production instances | Yes |
| `SYSTEM_SUGGESTIONS_TRUSTED_IP_HEADER` | `x-vercel-forwarded-for` after real entry verification | Same verified Vercel contract | No |
| `DEEPSEEK_API_KEY` | Existing safely stored key | Existing safely stored key | Yes |
| `SYSTEM_SUGGESTIONS_PROVIDER` | `auto` | `auto` | No |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | Same | No |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | Same | No |
| `SYSTEM_SUGGESTIONS_TIMEOUT_MS` | Retain the verified provider configuration | Same | No |

Do not upload `.env.local`, `.local/`, browser profiles, QA raw data, node_modules, `.next`, `.vercel`, or `.mgda-private-public`. Do not configure a local Redis URL, run/build-based namespace, or disabled TLS certificate verification. `SYSTEM_SUGGESTS_TEST_REDIS_URL` belongs only to isolated tests.

## Aiven for Valkey Free (first alternative, no vendor SDK required)

Owner steps: log in/create owner account; select **Valkey Free**, not a credit trial; confirm its zero-price plan with no paid upgrade/payment method; obtain the service URI from Overview; safely inject it as `REDIS_URL`. The Free service's cloud/region are provider-selected. Inspect the actual memory eviction policy; limit counters must not be evicted early. Retain fail-closed guidance behavior if writes fail. Do not buy advanced ACL/HA to pass this checklist.

Aiven currently documents a single node, 1 GB RAM with maxmemory 50%, no time limit, no SLA, possible idle shutdown, and provider changes to location/configuration. The default TLS certificate is browser-recognized; use certificate validation. Actual service compatibility is a runtime test, not inferred from the product name.

From `frontend`, `npm run check:hosted-redis` checks only format/presence (nonzero when incomplete). `npm run verify:hosted-redis -- --run` performs TLS/auth and the real application Lua counter, two independent cold workers/100 requests, global surface bucket, expiry and connection reuse. It creates only unique expiring test keys, makes zero provider calls, and never pauses, resets, restarts or flushes the hosted service. Failure injection remains on isolated resources with provider spies. Hosted results and actual Vercel forwarding-header overwrite/origin behavior must be reported separately.

Sources: [Free limits](https://aiven.io/docs/products/valkey/concepts/valkey-free-tier), [TLS](https://aiven.io/docs/platform/concepts/tls-ssl-certificates), [Vercel headers](https://vercel.com/docs/headers/request-headers).

## Clean checkout and regression

Use a fresh clone of the reviewed remote branch/SHA, not a dirty workstation copy. In `frontend`, run `npm ci`, then `MGDA_EPHEMERAL_BUILD=1 npm run build:vercel` for local/CI staging (Vercel itself sets `VERCEL=1`). The helper deliberately refuses the owner's redesign working tree. It requires no manually deleted files, local credentials or temporary QA assets.

Run `npm run audit:mobile-desktop-coupling`, `npm run test:vercel-public`, `npm run test:machine-reading`, and the affected Search/System Suggests regressions. After production start, run `MGDA_BASE_URL=<local URL> npm run test:machine-reading -- --require-http` and `npm run test:mobile-safe-area` with the same URL. Browser engines are pinned in the lockfile; install with `npx playwright install chromium webkit` (`--with-deps` on Linux). Product CI includes both engines and the safe production build.

Mobile layout: nav owns top inset; shell owns side/bottom; fixed overlay owns its own side/bottom; Top button offsets itself from the physical screen. ResizeObserver publishes actual nav height. Home pinned scenes use stable svh; Search alone follows visualViewport at normal zoom. Root and mobile shell use the existing paper token before hydration. Nonzero inset and viewport reductions in Playwright are simulations, not OS keyboard or iPhone evidence.

At the first protected URL, before a domain change, complete these **six real-phone checks**:
1. Cold-open Home, scroll with address bar expanded/collapsed: no edge flashes or scene reset.
2. Open/close Search: continuous overlay, correct nav edge and restored page scroll.
3. Focus query, open/close keyboard, scroll results: input/close accessible, no residual blank region.
4. Rotate with Search open: side controls clear notches and no horizontal clipping.
5. Index → Object → Back: filters/position retained and no doubled inset.
6. About/Source bottom and Top control, plus Context/Exploration PNG on supported desktop: last content/actions remain accessible.

Rollback by selecting a previously reviewed full candidate and rebuilding through this same command. Do not revert to main that lacks P0 safety fixes or clear Redis counters on app restart. No remote rollback exists until a deployment is actually made.
