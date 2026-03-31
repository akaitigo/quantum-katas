import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { setMockMode } from "@/lib/api";
import { KataList } from "./KataList";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function Wrapper({
    children,
  }: {
    readonly children: React.ReactNode;
  }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  };
}

describe("KataList", () => {
  beforeEach(() => {
    setMockMode(true);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("renders kata titles from mock data", async () => {
    render(<KataList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("量子ビットの基礎")).toBeInTheDocument();
    });
  });

  it("renders all three category sections", async () => {
    render(<KataList />, { wrapper: createWrapper() });

    await waitFor(() => {
      const headings = screen.getAllByRole("heading", { level: 2 });
      const headingTexts = headings.map((h) => h.textContent);
      expect(headingTexts.some((t) => t?.includes("Basics"))).toBe(true);
      expect(headingTexts.some((t) => t?.includes("Entanglement"))).toBe(true);
      expect(headingTexts.some((t) => t?.includes("Algorithms"))).toBe(true);
    });
  });

  it("renders difficulty badges", async () => {
    render(<KataList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("1/10")).toBeInTheDocument();
    });
  });

  it("renders progress bar with 0 completed", async () => {
    render(<KataList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("0/10 完了")).toBeInTheDocument();
    });
  });

  it("shows mock banner when in mock mode", async () => {
    render(<KataList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(
        screen.getByText("バックエンド未接続 — モックデータで表示しています"),
      ).toBeInTheDocument();
    });
  });

  it("renders kata cards as links", async () => {
    render(<KataList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("量子ビットの基礎")).toBeInTheDocument();
    });

    const firstKataLink = screen.getByText("量子ビットの基礎").closest("a");
    expect(firstKataLink).toHaveAttribute("href", "/kata/01-single-qubit");
  });
});
