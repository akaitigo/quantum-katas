import { TOTAL_KATAS } from "@/lib/constants";

interface ProgressBarProps {
  readonly completedCount: number;
}

export function ProgressBar({
  completedCount,
}: ProgressBarProps): React.JSX.Element {
  const percent = Math.round((completedCount / TOTAL_KATAS) * 100);

  return (
    <div className="progress-bar-container">
      <div
        className="progress-bar"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        tabIndex={0}
        aria-label={`進捗: ${String(percent)}%`}
      >
        <div
          className="progress-bar-fill"
          style={{ width: `${String(percent)}%` }}
        />
      </div>
      <span className="progress-text">
        {completedCount}/{TOTAL_KATAS} 完了
      </span>
    </div>
  );
}
