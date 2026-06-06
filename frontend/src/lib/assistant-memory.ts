export interface StoredAssistantMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  mode?: "send" | "research";
}

export interface AssistantMemoryContext {
  surfaceId?: string;
  title?: string;
  dateText?: string;
  sourceName?: string;
}

interface PageMemory {
  updatedAt: number;
  messages: StoredAssistantMessage[];
}

interface AssistantMemoryStore {
  lastPageKey: string | null;
  pageSwitches: number;
  pages: Record<string, PageMemory>;
}

const MEMORY_TTL_MS = 3 * 60 * 1000;
const MAX_PAGE_SWITCHES = 3;
const STORAGE_KEY = "archive-assistant-memory-v1";

let memoryStore: AssistantMemoryStore = {
  lastPageKey: null,
  pageSwitches: 0,
  pages: {},
};
let loadedFromStorage = false;

function now() {
  return Date.now();
}

function browserStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage ?? null;
}

function loadStore() {
  if (loadedFromStorage) return memoryStore;
  loadedFromStorage = true;
  const storage = browserStorage();
  if (!storage) return memoryStore;
  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return memoryStore;
    const parsed = JSON.parse(raw) as AssistantMemoryStore;
    if (parsed && typeof parsed === "object" && parsed.pages) {
      memoryStore = parsed;
    }
  } catch {
    memoryStore = { lastPageKey: null, pageSwitches: 0, pages: {} };
  }
  return memoryStore;
}

function saveStore() {
  const storage = browserStorage();
  if (!storage) return;
  try {
    storage.setItem(STORAGE_KEY, JSON.stringify(memoryStore));
  } catch {
    // Browser storage is an optimization; assistant memory still works in RAM.
  }
}

function pruneExpired(referenceTime = now()) {
  const store = loadStore();
  for (const [key, page] of Object.entries(store.pages)) {
    if (referenceTime - page.updatedAt > MEMORY_TTL_MS) {
      delete store.pages[key];
    }
  }
}

function clearAll() {
  memoryStore.pages = {};
  memoryStore.pageSwitches = 0;
}

function normalizeKeyPart(value?: string | number | null) {
  return String(value ?? "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 120);
}

export function assistantPageKey(context?: AssistantMemoryContext | null) {
  if (!context) return "archive-context";
  if (context.surfaceId) return `surface:${context.surfaceId}`;
  return [
    "context",
    normalizeKeyPart(context.title),
    normalizeKeyPart(context.dateText),
    normalizeKeyPart(context.sourceName),
  ]
    .filter(Boolean)
    .join(":");
}

export function loadAssistantMessages(pageKey: string): StoredAssistantMessage[] {
  const store = loadStore();
  pruneExpired();

  if (store.lastPageKey && store.lastPageKey !== pageKey) {
    store.pageSwitches += 1;
    if (store.pageSwitches > MAX_PAGE_SWITCHES) {
      clearAll();
    }
  }
  store.lastPageKey = pageKey;
  saveStore();

  return [...(store.pages[pageKey]?.messages ?? [])];
}

export function saveAssistantMessages(
  pageKey: string,
  messages: StoredAssistantMessage[],
) {
  const store = loadStore();
  pruneExpired();
  store.pages[pageKey] = {
    updatedAt: now(),
    messages: messages.slice(-12),
  };
  store.lastPageKey = pageKey;
  if (messages.length > 0) {
    store.pageSwitches = 0;
  }
  saveStore();
}
