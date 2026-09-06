import "server-only";
import { createHmac } from "node:crypto";
import { isIP } from "node:net";
import Redis from "ioredis";

type Environment = Readonly<Record<string, string | undefined>>;
export type RateLimitResult =
  | { status: "ALLOWED" | "LIMIT_REACHED"; remaining: number; retryAfter: number; resetAt: number }
  | { status: "LIMITER_UNAVAILABLE"; remaining: null; retryAfter: null; resetAt: null };
export const UNAVAILABLE: RateLimitResult = { status: "LIMITER_UNAVAILABLE", remaining: null, retryAfter: null, resetAt: null };
export const FIXED_WINDOW_SCRIPT = `
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('PEXPIRE', KEYS[1], ARGV[1]) end
return {count, redis.call('PTTL', KEYS[1])}
`;
const WINDOW_MS = 60_000;
const LIMIT = 30;
const OPERATION_MS = 500;
let connection: Redis | undefined;
let connectionUrl: string | undefined;

export function makeLimiterClient(url: string): Redis {
  const client = new Redis(url, { lazyConnect: true, connectTimeout: 300, commandTimeout: OPERATION_MS,
    maxRetriesPerRequest: 0, enableOfflineQueue: false, autoResendUnfulfilledCommands: false, retryStrategy: () => null });
  client.on("error", () => {}); // No credentials, addresses or raw errors in logs.
  return client;
}

// All cold requests await one bounded connection attempt, then each counts once.
// Never replay an EVAL whose result is unknown.
const pendingConnections = new WeakMap<Redis, Promise<void>>();
function ensureReady(client: Redis): Promise<void> {
  if (client.status === "ready") return Promise.resolve();
  const pending = pendingConnections.get(client);
  if (pending) return pending;
  const next = client.status === "wait" || client.status === "end"
    ? client.connect()
    : new Promise<void>((resolve, reject) => {
      const cleanup = () => { client.off("ready", ready); client.off("error", failed); client.off("end", ended); };
      const ready = () => { cleanup(); resolve(); };
      const failed = (error: Error) => { cleanup(); reject(error); };
      const ended = () => failed(new Error("limiter connection ended"));
      client.once("ready", ready); client.once("error", failed); client.once("end", ended);
    });
  pendingConnections.set(client, next);
  void next.then(() => pendingConnections.delete(client), () => pendingConnections.delete(client));
  return next;
}

export function requesterIdentity(request: Request, env: Environment): string | null {
  const secret = env.SYSTEM_SUGGESTIONS_IDENTITY_SECRET;
  if (!secret || secret.length < 32) return null;
  // Trust only an explicitly configured single-IP header overwritten by the ingress.
  // Without such a contract all anonymous traffic shares a conservative global bucket.
  const header = env.SYSTEM_SUGGESTIONS_TRUSTED_IP_HEADER?.trim().toLowerCase();
  const value = header ? request.headers.get(header)?.trim() : "anonymous";
  if (!value || (header && !isIP(value))) return null;
  const canonical = header && isIP(value) === 6 ? new URL(`http://[${value}]/`).hostname : value;
  return createHmac("sha256", secret).update(canonical).digest("hex");
}

export async function consumeFixedWindow(client: Redis, key: string, windowMs = WINDOW_MS, limit = LIMIT): Promise<RateLimitResult> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    const result = await Promise.race([
      (async () => {
        await ensureReady(client);
        return client.eval(FIXED_WINDOW_SCRIPT, 1, key, windowMs);
      })(),
      new Promise<never>((_, reject) => { timer = setTimeout(() => { client.disconnect(); reject(new Error("limiter timeout")); }, OPERATION_MS); }),
    ]);
    if (!Array.isArray(result) || result.length !== 2) return UNAVAILABLE;
    const [count, ttl] = result.map(Number);
    if (!Number.isSafeInteger(count) || count! < 1 || !Number.isSafeInteger(ttl) || ttl! < 0 || ttl! > windowMs) return UNAVAILABLE;
    return { status: count! <= limit ? "ALLOWED" : "LIMIT_REACHED", remaining: Math.max(0, limit - count!), retryAfter: Math.max(1, Math.ceil(ttl! / 1000)), resetAt: Date.now() + ttl! };
  } catch { return UNAVAILABLE; }
  finally { if (timer) clearTimeout(timer); }
}

export async function checkRequestRateLimit(request: Request, env: Environment = process.env): Promise<RateLimitResult> {
  const url = env.REDIS_URL;
  const namespace = env.SYSTEM_SUGGESTIONS_RATE_LIMIT_NAMESPACE;
  let identity: string | null;
  try { identity = requesterIdentity(request, env); } catch { return UNAVAILABLE; }
  if (!url || !identity || !namespace || !/^[a-zA-Z0-9:_-]{1,100}$/.test(namespace)) return UNAVAILABLE;
  if (env.NODE_ENV === "production" && namespace.startsWith("test:")) return UNAVAILABLE;
  if (env.NODE_ENV === "test" && !namespace.startsWith("test:")) return UNAVAILABLE;
  try {
    if (!connection || connectionUrl !== url) {
      connection?.disconnect();
      connection = makeLimiterClient(url);
      connectionUrl = url;
    }
    return await consumeFixedWindow(connection, `${namespace}:http:${identity}`);
  } catch { return UNAVAILABLE; }
}
