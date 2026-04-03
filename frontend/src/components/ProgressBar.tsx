interface ProgressBarProps {
  readonly completedCount: number;
  readonly totalKatas: number;
}

export function ProgressBar({
  completedCount,
  totalKatas,
}: ProgressBarProps): React.JSX.Element {
  const percent =
    totalKatas > 0 ? Math.round((completedCount / totalKatas) * 100) : 0;

  return (
    <div className="progress-bar-container">
      <div
        className="progress-bar"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`進捗: ${String(percent)}%`}
      >
        <div
          className="progress-bar-fill"
          style={{ width: `${String(percent)}%` }}
        />
      </div>
      <span className="progress-text">
        {completedCount}/{totalKatas} 完了
      </span>
    </div>
  );
}
