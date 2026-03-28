import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  fetchKataDetail,
  fetchKatas,
  isMockMode,
  setMockMode,
  validateKata,
} from "./api";

describe("API client (mock mode)", () => {
  beforeEach(() => {
    setMockMode(true);
  });

  afterEach(() => {
    setMockMode(false);
  });

  it("should report mock mode correctly", () => {
    expect(isMockMode()).toBe(true);
  });

  it("fetchKatas returns mock kata summaries", async () => {
    const katas = await fetchKatas();
    expect(katas.length).toBe(10);
    expect(katas[0]?.id).toBe("01-single-qubit");
    expect(katas[0]?.title).toBe("量子ビットの基礎");
    expect(katas[0]?.difficulty).toBe(1);
    expect(katas[0]?.category).toBe("basics");
  });

  it("fetchKataDetail returns detail for valid ID", async () => {
    const kata = await fetchKataDetail("01-single-qubit");
    expect(kata).not.toBeNull();
    expect(kata?.id).toBe("01-single-qubit");
    expect(kata?.title).toBe("量子ビットの基礎");
    expect(kata?.template_code).toContain("import cirq");
    expect(kata?.hints.length).toBeGreaterThan(0);
  });

  it("fetchKataDetail returns fallback detail for katas without explicit detail", async () => {
    const kata = await fetchKataDetail("05-pauli-z-gate");
    expect(kata).not.toBeNull();
    expect(kata?.id).toBe("05-pauli-z-gate");
    expect(kata?.title).toBe("Pauli-Z ゲート (位相反転)");
  });

  it("fetchKataDetail returns null for unknown ID", async () => {
    const kata = await fetchKataDetail("nonexistent");
    expect(kata).toBeNull();
  });

  it("validateKata returns mock response", async () => {
    const result = await validateKata("01-single-qubit", "import cirq");
    expect(result.passed).toBe(false);
    expect(result.message).toContain("モックモード");
  });
});
