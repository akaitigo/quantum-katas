import type { ExecutionResult as ExecutionResultType } from "@/types/execution";
import type { ValidateResponse } from "@/types/kata";

interface ExecutionResultProps {
  readonly executionResult: ExecutionResultType | null;
  readonly validationResult: ValidateResponse | null;
  readonly isExecuting: boolean;
  readonly isValidating: boolean;
}

function LoadingSpinner({
  message,
}: { readonly message: string }): React.JSX.Element {
  return (
    <div className="execution-loading" data-testid="execution-loading">
      <div className="loading-spinner" />
      <span>{message}</span>
    </div>
  );
}

function OutputBlock({
  label,
  content,
}: {
  readonly label: string;
  readonly content: string;
}): React.JSX.Element | null {
  if (!content) return null;

  return (
    <div className="output-block">
      <div className="output-label">{label}</div>
      <pre className="output-content">{content}</pre>
    </div>
  );
}

function CircuitDiagram({
  stdout,
}: { readonly stdout: string }): React.JSX.Element | null {
  // Detect Cirq circuit output patterns (lines with dashes, pipes, and gate symbols)
  const circuitPattern = /^[0-9a-z_]+(\(\d+\))?:\s*[-─|×@H#TXYZMS\s]+/m;
  if (!stdout || !circuitPattern.test(stdout)) return null;

  // Extract circuit diagram lines
  const lines = stdout.split("\n");
  const circuitLines: string[] = [];
  let inCircuit = false;

  for (const line of lines) {
    if (circuitPattern.test(line) || (inCircuit && /^[\s|─×@]/.test(line))) {
      circuitLines.push(line);
      inCircuit = true;
    } else if (inCircuit && line.trim() === "") {
      circuitLines.push(line);
      inCircuit = false;
    }
  }

  if (circuitLines.length === 0) return null;

  return (
    <div className="circuit-diagram">
      <div className="output-label">Circuit Diagram</div>
      <pre className="circuit-content">{circuitLines.join("\n")}</pre>
    </div>
  );
}

function ExecutionOutput({
  result,
}: {
  readonly result: ExecutionResultType;
}): React.JSX.Element {
  return (
    <div
      className={`execution-result ${result.success ? "execution-success" : "execution-error"}`}
      data-testid="execution-result"
    >
      <div className="execution-status">
        <span
          className={`status-indicator ${result.success ? "status-success" : "status-error"}`}
        />
        <span className="status-text">
          {result.success ? "実行成功" : "実行エラー"}
        </span>
      </div>

      {result.error && (
        <div className="execution-error-message">{result.error}</div>
      )}

      <CircuitDiagram stdout={result.stdout} />
      <OutputBlock label="stdout" content={result.stdout} />
      <OutputBlock label="stderr" content={result.stderr} />
    </div>
  );
}

function ValidationOutput({
  result,
}: {
  readonly result: ValidateResponse;
}): React.JSX.Element {
  return (
    <div
      className={`result-panel ${result.passed ? "result-passed" : "result-failed"}`}
      data-testid="validation-result"
    >
      <div
        className={`result-title ${result.passed ? "result-title-passed" : "result-title-failed"}`}
      >
        {result.passed ? "正解!" : "不正解"}
      </div>
      <div className="result-message">{result.message}</div>

      <CircuitDiagram stdout={result.stdout} />
      <OutputBlock label="stdout" content={result.stdout} />
      <OutputBlock label="stderr" content={result.stderr} />
    </div>
  );
}

export function ExecutionResult({
  executionResult,
  validationResult,
  isExecuting,
  isValidating,
}: ExecutionResultProps): React.JSX.Element | null {
  if (isExecuting) {
    return <LoadingSpinner message="コードを実行中..." />;
  }

  if (isValidating) {
    return <LoadingSpinner message="コードを検証中..." />;
  }

  if (!executionResult && !validationResult) {
    return null;
  }

  return (
    <div
      className="execution-result-container"
      data-testid="execution-result-container"
    >
      {validationResult && <ValidationOutput result={validationResult} />}
      {executionResult && !validationResult && (
        <ExecutionOutput result={executionResult} />
      )}
    </div>
  );
}
