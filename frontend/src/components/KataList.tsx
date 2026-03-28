import { useKataList } from "@/hooks/useKatas";
import { useProgress } from "@/hooks/useProgress";
import { isMockMode } from "@/lib/api";
import { CATEGORY_LABELS, CATEGORY_ORDER, TOTAL_KATAS } from "@/lib/constants";
import type { KataSummary } from "@/types/kata";
import { Link } from "react-router-dom";
import { ProgressBar } from "./ProgressBar";

function DifficultyBadge({
  difficulty,
}: { readonly difficulty: number }): React.JSX.Element {
  return <span className="badge badge-difficulty">{difficulty}/10</span>;
}

function CategoryBadge({
  category,
}: { readonly category: string }): React.JSX.Element {
  const label = CATEGORY_LABELS[category] ?? category;
  return (
    <span className={`badge badge-category badge-category-${category}`}>
      {label}
    </span>
  );
}

function KataCard({
  kata,
  completed,
  prerequisitesMet,
}: {
  readonly kata: KataSummary;
  readonly completed: boolean;
  readonly prerequisitesMet: boolean;
}): React.JSX.Element {
  return (
    <Link
      to={`/kata/${kata.id}`}
      className={`kata-card ${completed ? "kata-card-completed" : ""}`}
      aria-label={`${kata.title} — 難易度 ${String(kata.difficulty)}`}
    >
      <div className="kata-card-header">
        <span className="kata-card-title">{kata.title}</span>
        <span className="completion-icon" aria-hidden="true">
          {completed ? "\u2705" : prerequisitesMet ? "\u26AA" : "\u{1F512}"}
        </span>
      </div>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        <DifficultyBadge difficulty={kata.difficulty} />
        <CategoryBadge category={kata.category} />
      </div>
      {kata.prerequisites.length > 0 && (
        <div className="kata-card-prereqs">
          前提: {kata.prerequisites.join(", ")}
        </div>
      )}
    </Link>
  );
}

export function KataList(): React.JSX.Element {
  const { katas, isLoading, error } = useKataList();
  const { isCompleted, completedCount } = useProgress();

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <p>カタを読み込み中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">読み込みに失敗しました: {error.message}</p>
      </div>
    );
  }

  const grouped = new Map<string, KataSummary[]>();
  for (const category of CATEGORY_ORDER) {
    grouped.set(category, []);
  }
  for (const kata of katas) {
    const list = grouped.get(kata.category);
    if (list) {
      list.push(kata);
    } else {
      grouped.set(kata.category, [kata]);
    }
  }

  const isAllClear = completedCount >= TOTAL_KATAS;

  return (
    <div>
      {isMockMode() && (
        <div className="mock-banner">
          バックエンド未接続 — モックデータで表示しています
        </div>
      )}

      <div style={{ marginBottom: "2rem" }}>
        <ProgressBar completedCount={completedCount} />
      </div>

      {isAllClear && (
        <div className="celebration-banner" data-testid="celebration-banner">
          <div className="celebration-title">All Clear!</div>
          <p className="celebration-message">
            全10カタを制覇しました。量子コンピューティングの基礎をマスターです!
          </p>
        </div>
      )}

      {CATEGORY_ORDER.map((category) => {
        const categoryKatas = grouped.get(category);
        if (!categoryKatas || categoryKatas.length === 0) return null;

        return (
          <section key={category} className="category-section">
            <h2 className="category-title">
              <CategoryBadge category={category} />
              {CATEGORY_LABELS[category] ?? category}
            </h2>
            <div className="kata-grid">
              {categoryKatas.map((kata) => {
                const completed = isCompleted(kata.id);
                const prerequisitesMet = kata.prerequisites.every((preId) =>
                  isCompleted(preId),
                );
                return (
                  <KataCard
                    key={kata.id}
                    kata={kata}
                    completed={completed}
                    prerequisitesMet={prerequisitesMet}
                  />
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
