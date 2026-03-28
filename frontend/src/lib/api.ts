import type { KataDetail, KataSummary, ValidateResponse } from "@/types/kata";
import { API_BASE_URL } from "./constants";
import {
  MOCK_KATA_SUMMARIES,
  getMockKataDetail,
  getMockValidateResponse,
} from "./mock-data";

/** Whether to use mock data instead of the real backend. */
let useMock = false;

/** Detect if the backend is reachable; fall back to mock if not. */
async function detectBackend(): Promise<boolean> {
  try {
    const res = await fetch("/health", { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

let backendChecked = false;

async function ensureBackendDetected(): Promise<void> {
  if (backendChecked) return;
  backendChecked = true;
  const available = await detectBackend();
  useMock = !available;
}

class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new ApiError(res.status, text);
  }
  return res.json() as Promise<T>;
}

/** Fetch the list of all katas. */
export async function fetchKatas(): Promise<KataSummary[]> {
  await ensureBackendDetected();
  if (useMock) {
    return [...MOCK_KATA_SUMMARIES];
  }
  return fetchJson<KataSummary[]>("/katas");
}

/** Fetch detail for a single kata by ID. */
export async function fetchKataDetail(
  kataId: string,
): Promise<KataDetail | null> {
  await ensureBackendDetected();
  if (useMock) {
    return getMockKataDetail(kataId) ?? null;
  }
  try {
    return await fetchJson<KataDetail>(`/katas/${kataId}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

/** Validate user code against a kata. */
export async function validateKata(
  kataId: string,
  code: string,
): Promise<ValidateResponse> {
  await ensureBackendDetected();
  if (useMock) {
    return getMockValidateResponse(kataId, code);
  }
  return fetchJson<ValidateResponse>(`/katas/${kataId}/validate`, {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

/** Check if we are operating in mock mode. */
export function isMockMode(): boolean {
  return useMock;
}

/** Force mock mode on/off (useful for testing). */
export function setMockMode(mock: boolean): void {
  useMock = mock;
  backendChecked = true;
}
