/** Lightweight kata representation used in list endpoints. */
export interface KataSummary {
  readonly id: string;
  readonly title: string;
  readonly difficulty: number;
  readonly category: string;
  readonly prerequisites: readonly string[];
}

/** Kata detail returned by GET /api/katas/:id (excludes solution_code). */
export interface KataDetail {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly difficulty: number;
  readonly category: string;
  readonly template_code: string;
  readonly hints: readonly string[];
  readonly prerequisites: readonly string[];
  readonly explanation: string;
}

/** Request body for POST /api/katas/:id/validate. */
export interface ValidateRequest {
  readonly code: string;
}

/** Response body from POST /api/katas/:id/validate. */
export interface ValidateResponse {
  readonly passed: boolean;
  readonly message: string;
  readonly stdout: string;
  readonly stderr: string;
}
