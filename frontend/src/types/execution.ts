/** Response body from POST /api/execute. */
export interface ExecutionResult {
  readonly stdout: string;
  readonly stderr: string;
  readonly success: boolean;
  readonly error: string | null;
}
