# System Suggestions setup

System Suggestions is optional. With no key, an explicit static/off mode, a timeout, provider failure, invalid response, unsafe note, or unapproved suggestion ID, the server returns deterministic fallback guidance. Search and TRACE core behavior never depends on this setup.

## Exact key setup

Run from the repository root:

```bash
git check-ignore -q frontend/.env.local && echo "frontend/.env.local is ignored"
npm --prefix frontend run setup:deepseek-key
git check-ignore -q frontend/.env.local && echo "frontend/.env.local remains ignored"
stat -f '%Lp %N' frontend/.env.local
```

The committed helper prompts in an interactive terminal with echo disabled, creates or updates only `DEEPSEEK_API_KEY` in `frontend/.env.local`, preserves every unrelated line, atomically replaces the file, sets mode `600`, and never prints the key. It refuses a symbolic-link target or an unignored destination. Do not commit `.env.local`.

Expected committed public configuration is in `frontend/.env.example`:

```text
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
SYSTEM_SUGGESTIONS_PROVIDER=auto
SYSTEM_SUGGESTIONS_TIMEOUT_MS=2500
```

No environment name begins with `NEXT_PUBLIC_`. Safe code defaults enforce the official base URL, `/responses` API, and exact `deepseek-v4-flash` model even if an unsupported environment value is supplied.

## Enable, disable, and test fallback

From `frontend/`, stop the current Next.js process with `Ctrl-C`, then use exactly one of these starts:

```bash
# Enable automatic provider selection: provider when a key exists, fallback otherwise.
SYSTEM_SUGGESTIONS_PROVIDER=auto npm run dev

# Disable provider calls and force deterministic fallback.
SYSTEM_SUGGESTIONS_PROVIDER=static npm run dev

# Test fallback with an explicitly empty process key, without editing .env.local.
DEEPSEEK_API_KEY= SYSTEM_SUGGESTIONS_PROVIDER=static npm run dev
```

After a provider/environment change, restart the Next.js process; environment values are read by the server process. `off` is accepted as a synonym for `static`.

For the automated no-key/failure contract:

```bash
cd frontend
npm run test:system-suggestions
```

The suite injects an empty server environment and mocked failures. It performs no external provider call.

## Verify the browser bundle

After a local production build, run:

```bash
cd frontend
npm run build
npm run verify:no-client-key
```

The verifier reads the local key without printing it and scans `.next/static`. A successful result is `CLIENT_KEY_BUNDLE_SCAN=PASS MATCH_COUNT=0` (or an explicit no-key/empty-key pass). Do not use shell commands that echo the key or pass its literal value on a command line.

## Runtime and disclosure boundary

The key is read only by server-only code and is carried only in the provider Authorization header. It is never returned by the API, placed in prompt text, logged, included in error detail, or referenced by client code. Public Search and TRACE pages show only `System suggests`; provider identity and source-class audit fields are not rendered. The About/Methodology page contains the public disclosure.
