import { useKataList } from "@/hooks/useKatas";
import { useKataDetail } from "@/hooks/useKatas";
import { useProgress } from "@/hooks/useProgress";
import { isMockMode, validateKata } from "@/lib/api";
import { CATEGORY_LABELS } from "@/lib/constants";
import type { ValidateResponse } from "@/types/kata";
import { useCallback, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

function HintPanel({
  hints,
}: { readonly hints: readonly string[] }): React.JSX.Element {
  const [visibleCount, setVisibleCount] = useState(0);

  const showNextHint = useCallback(() => {
    setVisibleCount((prev) => Math.min(prev + 1, hints.length));
  }, [hints.length]);

  if (hints.length === 0) return <></>;

  return (
    <div className="hints-section">
      {hints.slice(0, visibleCount).map((hint, index) => (
        <div key={`hint-${String(index)}`} className="hint-item">
          <div className="hint-label">Hint {index + 1}</div>
          <div>{hint}</div>
        </div>
      ))}
      {visibleCount < hints.length && (
        <button
          type="button"
          className="btn btn-secondary"
          onClick={showNextHint}
        >
          Hint {visibleCount + 1} を表示 ({hints.length - visibleCount} 残り)
        </button>
      )}
    </div>
  );
}

function ResultDisplay({
  result,
}: { readonly result: ValidateResponse }): React.JSX.Element {
  const passed = result.passed;

  return (
    <div
      className={`result-panel ${passed ? "result-passed" : "result-failed"}`}
    >
      <div
        className={`result-title ${passed ? "result-title-passed" : "result-title-failed"}`}
      >
        {passed ? "正解!" : "不正解"}
      </div>
      <div className="result-message">{result.message}</div>
      {result.stdout && (
        <div>
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--color-text-muted)",
              marginBottom: "0.25rem",
            }}
          >
            stdout:
          </div>
          <div className="result-output">{result.stdout}</div>
        </div>
      )}
      {result.stderr && (
        <div style={{ marginTop: "0.5rem" }}>
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--color-text-muted)",
              marginBottom: "0.25rem",
            }}
          >
            stderr:
          </div>
          <div className="result-output">{result.stderr}</div>
        </div>
      )}
    </div>
  );
}

export function KataDetail(): React.JSX.Element {
  const { kataId } = useParams<{ kataId: string }>();
  const resolvedId = kataId ?? "";

  const { kata, isLoading, error } = useKataDetail(resolvedId);
  const { katas } = useKataList();
  const { isCompleted, markCompleted } = useProgress();

  const [code, setCode] = useState<string | null>(null);
  const [validationResult, setValidationResult] =
    useState<ValidateResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Determine prev / next katas based on ordered list
  const { prevKata, nextKata } = useMemo(() => {
    if (katas.length === 0) return { prevKata: null, nextKata: null };
    const currentIndex = katas.findIndex((k) => k.id === resolvedId);
    if (currentIndex === -1) return { prevKata: null, nextKata: null };
    return {
      prevKata: currentIndex > 0 ? (katas[currentIndex - 1] ?? null) : null,
      nextKata:
        currentIndex < katas.length - 1
          ? (katas[currentIndex + 1] ?? null)
          : null,
    };
  }, [katas, resolvedId]);

  const handleValidate = useCallback(async () => {
    if (!kata || code === null) return;
    setIsValidating(true);
    try {
      const result = await validateKata(kata.id, code);
      setValidationResult(result);
      if (result.passed) {
        markCompleted(kata.id);
      }
    } catch (err) {
      setValidationResult({
        passed: false,
        message:
          err instanceof Error ? err.message : "検証中にエラーが発生しました",
        stdout: "",
        stderr: "",
      });
    } finally {
      setIsValidating(false);
    }
  }, [kata, code, markCompleted]);

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
        <Link to="/" className="btn btn-secondary">
          カタ一覧に戻る
        </Link>
      </div>
    );
  }

  if (!kata) {
    return (
      <div className="error-container">
        <p className="error-message">カタが見つかりませんでした</p>
        <Link to="/" className="btn btn-secondary">
          カタ一覧に戻る
        </Link>
      </div>
    );
  }

  // Initialize code from template on first render for this kata
  const displayedCode = code ?? kata.template_code;

  return (
    <div className="kata-detail">
      {isMockMode() && (
        <div className="mock-banner">
          バックエンド未接続 — モックデータで表示しています
        </div>
      )}

      <div className="kata-detail-header">
        <Link
          to="/"
          className="nav-link"
          style={{ marginBottom: "0.75rem", display: "inline-flex" }}
        >
          &larr; カタ一覧
        </Link>
        <h1 className="kata-detail-title">
          {isCompleted(kata.id) && (
            <span style={{ marginRight: "0.5rem" }}>&#x2705;</span>
          )}
          {kata.title}
        </h1>
        <div className="kata-detail-meta">
          <span className="badge badge-difficulty">{kata.difficulty}/10</span>
          <span
            className={`badge badge-category badge-category-${kata.category}`}
          >
            {CATEGORY_LABELS[kata.category] ?? kata.category}
          </span>
        </div>
      </div>

      <div className="kata-detail-description">{kata.description}</div>

      {kata.explanation && (
        <div className="kata-detail-explanation">
          <pre>
            <code>{kata.explanation}</code>
          </pre>
        </div>
      )}

      <div className="editor-section">
        <h2 className="editor-section-title">Code Editor</h2>
        <textarea
          className="code-textarea"
          value={displayedCode}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          aria-label="コードエディタ"
        />
      </div>

      <div className="btn-group">
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => void handleValidate()}
          disabled={isValidating}
        >
          {isValidating ? "検証中..." : "実行"}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => setCode(kata.template_code)}
        >
          リセット
        </button>
      </div>

      {validationResult && (
        <div style={{ marginTop: "1rem" }}>
          <ResultDisplay result={validationResult} />
        </div>
      )}

      <HintPanel hints={kata.hints} />

      <nav className="kata-nav" aria-label="カタ間ナビゲーション">
        <div>
          {prevKata && (
            <Link to={`/kata/${prevKata.id}`} className="nav-link">
              &larr; {prevKata.title}
            </Link>
          )}
        </div>
        <div>
          {nextKata && (
            <Link to={`/kata/${nextKata.id}`} className="nav-link">
              {nextKata.title} &rarr;
            </Link>
          )}
        </div>
      </nav>
    </div>
  );
}
