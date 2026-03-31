import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setMockMode } from "@/lib/api";
import { KataDetail } from "./KataDetail";

// Mock Monaco Editor to avoid loading in test environment
vi.mock("@monaco-editor/react", () => {
  return {
    default: function MockEditor({
      value,
      onChange,
    }: {
      readonly value: string;
      readonly onChange?: (value: string | undefined) => void;
    }) {
      return (
        <textarea
          data-testid="monaco-editor-mock"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          aria-label="コードエディタ"
        />
      );
    },
  };
});

function renderWithRoute(kataId: string, allEntries?: string[]) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const entries = allEntries ?? [`/kata/${kataId}`];

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={entries}>
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

  it("renders the code editor with template code", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      const editor = screen.getByTestId("code-editor");
      expect(editor).toBeInTheDocument();
    });

    const textarea =
      screen.getByLabelText<HTMLTextAreaElement>("コードエディタ");
    expect(textarea.value).toContain("import cirq");
  });

  it("renders the execute button", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "実行" })).toBeInTheDocument();
    });
  });

  it("renders the submit button", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "提出" })).toBeInTheDocument();
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
      expect(screen.getByTestId("show-next-hint")).toBeInTheDocument();
    });

    await user.click(screen.getByTestId("show-next-hint"));
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

  it("renders result placeholder when no results", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(
        screen.getByText("コードを実行すると、ここに結果が表示されます"),
      ).toBeInTheDocument();
    });
  });

  it("renders the split layout with editor and result panels", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(screen.getByText("Code Editor")).toBeInTheDocument();
      expect(screen.getByText("実行結果")).toBeInTheDocument();
    });
  });

  it("renders hint panel with proper structure", async () => {
    renderWithRoute("01-single-qubit");

    await waitFor(() => {
      expect(screen.getByTestId("hint-panel")).toBeInTheDocument();
      expect(screen.getByText("Hints (0/3)")).toBeInTheDocument();
    });
  });

  it("resets editor code when navigating to a different kata", async () => {
    const user = userEvent.setup();
    renderWithRoute("01-single-qubit");

    // Wait for kata 01 to load
    await waitFor(() => {
      expect(screen.getByText("量子ビットの基礎")).toBeInTheDocument();
    });

    // Edit code in the editor
    const textarea =
      screen.getByLabelText<HTMLTextAreaElement>("コードエディタ");
    await user.clear(textarea);
    await user.type(textarea, "print('edited')");
    expect(textarea.value).toContain("edited");

    // Navigate to kata 02 via the bottom nav link (partial text match)
    const nextLink = screen.getByRole("link", {
      name: /Pauli-X/,
    });
    await user.click(nextLink);

    // Wait for kata 02 to load — editor should have kata 02 template, not kata 01 edits
    await waitFor(() => {
      const title = screen.getByRole("heading", { level: 1 });
      expect(title.textContent).toContain("Pauli-X");
    });

    const updatedTextarea =
      screen.getByLabelText<HTMLTextAreaElement>("コードエディタ");
    expect(updatedTextarea.value).not.toContain("edited");
    expect(updatedTextarea.value).toContain("cirq.LineQubit(0)");
  });

  it("resets hint count when navigating to a different kata", async () => {
    const user = userEvent.setup();
    renderWithRoute("01-single-qubit");

    // Wait for kata 01 to load
    await waitFor(() => {
      expect(screen.getByText("量子ビットの基礎")).toBeInTheDocument();
    });

    // Reveal a hint on kata 01
    await user.click(screen.getByTestId("show-next-hint"));
    expect(screen.getByText("Hints (1/3)")).toBeInTheDocument();

    // Navigate to kata 02 via the bottom nav link
    const nextLink = screen.getByRole("link", {
      name: /Pauli-X/,
    });
    await user.click(nextLink);

    // Hint count should reset to 0 for kata 02
    await waitFor(() => {
      expect(screen.getByText("Hints (0/3)")).toBeInTheDocument();
    });
  });
});
