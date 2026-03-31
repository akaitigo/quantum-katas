import { PROGRESS_STORAGE_KEY } from "@/lib/constants";
import { useCallback, useEffect, useState } from "react";

/** Key used to store hint visibility state in localStorage. */
const HINTS_STORAGE_KEY = `${PROGRESS_STORAGE_KEY}-hints`;

interface HintState {
  readonly [kataId: string]: number;
}

function loadHintState(): HintState {
  try {
    const raw = localStorage.getItem(HINTS_STORAGE_KEY);
    if (raw === null) return {};
    const parsed: unknown = JSON.parse(raw);
    if (
      typeof parsed !== "object" ||
      parsed === null ||
      Array.isArray(parsed)
    ) {
      return {};
    }
    const result: Record<string, number> = {};
    for (const [key, value] of Object.entries(
      parsed as Record<string, unknown>,
    )) {
      if (typeof value === "number") {
        result[key] = value;
      }
    }
    return result;
  } catch {
    return {};
  }
}

function saveHintState(state: HintState): void {
  localStorage.setItem(HINTS_STORAGE_KEY, JSON.stringify(state));
}

interface HintPanelProps {
  readonly kataId: string;
  readonly hints: readonly string[];
}

export function HintPanel({
  kataId,
  hints,
}: HintPanelProps): React.JSX.Element {
  const [visibleCount, setVisibleCount] = useState<number>(() => {
    const state = loadHintState();
    return state[kataId] ?? 0;
  });

  const [collapsedHints, setCollapsedHints] = useState<ReadonlySet<number>>(
    () => new Set<number>(),
  );

  // Re-initialise when switching to a different kata
  useEffect(() => {
    const state = loadHintState();
    setVisibleCount(state[kataId] ?? 0);
    setCollapsedHints(new Set<number>());
  }, [kataId]);

  const showNextHint = useCallback(() => {
    setVisibleCount((prev) => {
      const next = Math.min(prev + 1, hints.length);
      const state = loadHintState();
      saveHintState({ ...state, [kataId]: next });
      return next;
    });
  }, [hints.length, kataId]);

  const toggleHint = useCallback((index: number) => {
    setCollapsedHints((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }, []);

  if (hints.length === 0) return <></>;

  return (
    <div className="hints-section" data-testid="hint-panel">
      <h3 className="hints-title">
        Hints ({visibleCount}/{hints.length})
      </h3>
      {hints.slice(0, visibleCount).map((hint, index) => {
        const isCollapsed = collapsedHints.has(index);
        return (
          <button
            type="button"
            key={`hint-${String(index)}`}
            className={`hint-item hint-item-toggle ${isCollapsed ? "hint-collapsed" : ""}`}
            onClick={() => toggleHint(index)}
            aria-expanded={!isCollapsed}
            data-testid={`hint-${String(index)}`}
          >
            <div className="hint-header">
              <div className="hint-label">
                <span className="hint-icon" aria-hidden="true">
                  {"\u{1F4A1}"}
                </span>
                Hint {index + 1}
              </div>
              <span className="hint-chevron" aria-hidden="true">
                {isCollapsed ? "\u25B6" : "\u25BC"}
              </span>
            </div>
            {!isCollapsed && <div className="hint-content">{hint}</div>}
          </button>
        );
      })}
      {visibleCount < hints.length && (
        <button
          type="button"
          className="btn btn-hint"
          onClick={showNextHint}
          data-testid="show-next-hint"
        >
          <span aria-hidden="true">{"\u{1F4A1}"}</span>
          Hint {visibleCount + 1} を表示 ({hints.length - visibleCount} 残り)
        </button>
      )}
    </div>
  );
}
