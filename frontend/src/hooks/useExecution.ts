import { executeCode, isMockMode } from "@/lib/api";
import type { ExecutionResult } from "@/types/execution";
import { useCallback, useState } from "react";

interface UseExecutionReturn {
  readonly executionResult: ExecutionResult | null;
  readonly isExecuting: boolean;
  readonly execute: (code: string) => Promise<void>;
  readonly clearResult: () => void;
}

export function useExecution(): UseExecutionReturn {
  const [executionResult, setExecutionResult] =
    useState<ExecutionResult | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  const execute = useCallback(async (code: string) => {
    setIsExecuting(true);
    setExecutionResult(null);
    try {
      const result = await executeCode(code);
      setExecutionResult(result);
    } catch (err) {
      setExecutionResult({
        stdout: "",
        stderr:
          err instanceof Error ? err.message : "実行中にエラーが発生しました",
        success: false,
        error:
          err instanceof Error ? err.message : "実行中にエラーが発生しました",
      });
    } finally {
      setIsExecuting(false);
    }
  }, []);

  const clearResult = useCallback(() => {
    setExecutionResult(null);
  }, []);

  return {
    executionResult,
    isExecuting,
    execute,
    clearResult,
  };
}

/** Whether the backend is available for code execution. */
export function canExecute(): boolean {
  return !isMockMode();
}
