import type { FolderTypeKey } from "@/types/archive";

/** Shared folder inks without importing the large archive mock payload. */
export const FOLDER_INK: Record<FolderTypeKey, string> = {
  region: "#1F5FD1",
  theme: "#138B5E",
  medium: "#E83D3B",
  movement: "#7466D6",
};

export function getFolderInk(type: string): string {
  return FOLDER_INK[type as FolderTypeKey] ?? "#2E2925";
}

export function getFolderColor(type: string): string {
  return getFolderInk(type);
}
