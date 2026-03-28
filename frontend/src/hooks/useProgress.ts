import { PROGRESS_STORAGE_KEY } from "@/lib/constants";
import { useCallback, useSyncExternalStore } from "react";

/**
 * Progress store backed by localStorage.
 *
 * Stores a set of completed kata IDs and notifies subscribers on change.
 */
const listeners = new Set<() => void>();

function getSnapshot(): ReadonlySet<string> {
  try {
    const raw = localStorage.getItem(PROGRESS_STORAGE_KEY);
    if (raw === null) return new Set<string>();
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return new Set<string>();
    return new Set(parsed.filter((v): v is string => typeof v === "string"));
  } catch {
    return new Set<string>();
  }
}

let cachedSnapshot = getSnapshot();

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function emitChange(): void {
  cachedSnapshot = getSnapshot();
  for (const listener of listeners) {
    listener();
  }
}

function persist(ids: ReadonlySet<string>): void {
  localStorage.setItem(PROGRESS_STORAGE_KEY, JSON.stringify([...ids]));
  emitChange();
}

/**
 * Hook that provides access to kata completion progress.
 *
 * Progress is persisted in localStorage and survives page reloads.
 */
export function useProgress(): {
  completedKatas: ReadonlySet<string>;
  markCompleted: (kataId: string) => void;
  isCompleted: (kataId: string) => boolean;
  completedCount: number;
  resetProgress: () => void;
} {
  const completedKatas = useSyncExternalStore(
    subscribe,
    () => cachedSnapshot,
    () => cachedSnapshot,
  );

  const markCompleted = useCallback((kataId: string) => {
    const current = getSnapshot();
    const next = new Set(current);
    next.add(kataId);
    persist(next);
  }, []);

  const isCompleted = useCallback(
    (kataId: string) => completedKatas.has(kataId),
    [completedKatas],
  );

  const resetProgress = useCallback(() => {
    persist(new Set());
  }, []);

  return {
    completedKatas,
    markCompleted,
    isCompleted,
    completedCount: completedKatas.size,
    resetProgress,
  };
}
