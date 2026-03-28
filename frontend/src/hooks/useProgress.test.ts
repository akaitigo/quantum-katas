import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useProgress } from "./useProgress";

const STORAGE_KEY = "quantum-katas-progress";

describe("useProgress", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    // Reset internal cached snapshot by calling resetProgress
    const { result } = renderHook(() => useProgress());
    act(() => {
      result.current.resetProgress();
    });
  });

  it("starts with zero completed katas", () => {
    const { result } = renderHook(() => useProgress());
    expect(result.current.completedCount).toBe(0);
    expect(result.current.completedKatas.size).toBe(0);
  });

  it("marks a kata as completed", () => {
    const { result } = renderHook(() => useProgress());

    act(() => {
      result.current.markCompleted("01-single-qubit");
    });

    expect(result.current.isCompleted("01-single-qubit")).toBe(true);
    expect(result.current.completedCount).toBe(1);
  });

  it("persists progress to localStorage", () => {
    const { result } = renderHook(() => useProgress());

    act(() => {
      result.current.markCompleted("01-single-qubit");
    });

    const stored = localStorage.getItem(STORAGE_KEY);
    expect(stored).toBeTruthy();
    const parsed = JSON.parse(String(stored)) as string[];
    expect(parsed).toContain("01-single-qubit");
  });

  it("loads progress from localStorage via markCompleted roundtrip", () => {
    // The module-level cache in useProgress is shared across tests.
    // Instead of pre-seeding localStorage, we markCompleted, unmount, and re-mount.
    const { result: firstResult, unmount } = renderHook(() => useProgress());
    act(() => {
      firstResult.current.markCompleted("01-single-qubit");
      firstResult.current.markCompleted("02-pauli-x-gate");
    });
    unmount();

    // Re-mount — the hook should reflect localStorage state
    const { result } = renderHook(() => useProgress());
    expect(result.current.completedCount).toBe(2);
    expect(result.current.isCompleted("01-single-qubit")).toBe(true);
    expect(result.current.isCompleted("02-pauli-x-gate")).toBe(true);
  });

  it("does not duplicate already-completed katas", () => {
    const { result } = renderHook(() => useProgress());

    act(() => {
      result.current.markCompleted("01-single-qubit");
    });
    act(() => {
      result.current.markCompleted("01-single-qubit");
    });

    expect(result.current.completedCount).toBe(1);
  });

  it("resets progress", () => {
    const { result } = renderHook(() => useProgress());

    act(() => {
      result.current.markCompleted("01-single-qubit");
      result.current.markCompleted("02-pauli-x-gate");
    });

    act(() => {
      result.current.resetProgress();
    });

    expect(result.current.completedCount).toBe(0);
  });

  it("handles corrupted localStorage gracefully", () => {
    localStorage.setItem(STORAGE_KEY, "not-valid-json");

    const { result } = renderHook(() => useProgress());
    // Corrupted data should be treated as empty
    expect(result.current.completedCount).toBe(0);
  });

  it("handles non-array localStorage value gracefully", () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ wrong: "type" }));

    const { result } = renderHook(() => useProgress());
    expect(result.current.completedCount).toBe(0);
  });
});
