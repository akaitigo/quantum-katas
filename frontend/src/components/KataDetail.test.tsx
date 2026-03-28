import { setMockMode } from "@/lib/api";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { KataDetail } from "./KataDetail";

function renderWithRoute(kataId: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/kata/${kataId}`]}>
        <Routes>
          <Route path="/kata/:kataId" element={<KataDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("KataDetail", () => {
  beforeEach(() => {
    setMockMode(true);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("renders kata title", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(screen.getByText("量子ビットの基礎")).toBeInTheDocument();
    });
  });

  it("renders difficulty badge", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(screen.getByText("1/10")).toBeInTheDocument();
    });
  });

  it("renders the code textarea with template code", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      const textarea =
        screen.getByLabelText<HTMLTextAreaElement>("コードエディタ");
      expect(textarea).toBeInTheDocument();
      expect(textarea.value).toContain("import cirq");
    });
  });

  it("renders the execute button", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "実行" })).toBeInTheDocument();
    });
  });

  it("renders the reset button", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "リセット" }),
      ).toBeInTheDocument();
    });
  });

  it("shows hints progressively when hint button is clicked", async () => {
    const user = userEvent.setup();
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(screen.getByText(/Hint 1 を表示/)).toBeInTheDocument();
    });

    await user.click(screen.getByText(/Hint 1 を表示/));
    expect(screen.getByText("Hint 1")).toBeInTheDocument();
    expect(
      screen.getByText("cirq.LineQubit(0) で量子ビットを作成できます"),
    ).toBeInTheDocument();
  });

  it("renders back link to kata list", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      const backLink = screen.getByText(/カタ一覧/);
      expect(backLink).toBeInTheDocument();
      expect(backLink.closest("a")).toHaveAttribute("href", "/");
    });
  });

  it("shows not found message for invalid kata ID", async () => {
    renderWithRoute("nonexistent-kata");

    await waitFor(() => {
      expect(
        screen.getByText("カタが見つかりませんでした"),
      ).toBeInTheDocument();
    });
  });

  it("renders mock banner in mock mode", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(
        screen.getByText("バックエンド未接続 — モックデータで表示しています"),
      ).toBeInTheDocument();
    });
  });
});
