import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { HintPanel } from "./HintPanel";

const HINT_1 = "cirq.LineQubit(0) で量子ビットを作成できます";
const HINT_2 =
  "cirq.Circuit([cirq.measure(q, key='result')]) で測定回路を作成します";
const HINT_3 = "sim.run(circuit, repetitions=10) で実行します";
const HINTS = [HINT_1, HINT_2, HINT_3];

describe("HintPanel", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("renders nothing when there are no hints", () => {
    const { container } = render(<HintPanel kataId="test-kata" hints={[]} />);
    expect(container.textContent).toBe("");
  });

  it("renders hint count header", () => {
    render(<HintPanel kataId="test-kata" hints={HINTS} />);
    expect(screen.getByText("Hints (0/3)")).toBeInTheDocument();
  });

  it("shows show-next-hint button initially", () => {
    render(<HintPanel kataId="test-kata" hints={HINTS} />);
    expect(screen.getByTestId("show-next-hint")).toBeInTheDocument();
    expect(screen.getByText(/Hint 1 を表示/)).toBeInTheDocument();
  });

  it("reveals hints one by one when clicking the button", async () => {
    const user = userEvent.setup();
    render(<HintPanel kataId="test-kata" hints={HINTS} />);

    // Click to show hint 1
    await user.click(screen.getByTestId("show-next-hint"));
    expect(screen.getByText("Hints (1/3)")).toBeInTheDocument();
    expect(screen.getByText(HINT_1)).toBeInTheDocument();

    // Click to show hint 2
    await user.click(screen.getByTestId("show-next-hint"));
    expect(screen.getByText("Hints (2/3)")).toBeInTheDocument();
    expect(screen.getByText(HINT_2)).toBeInTheDocument();

    // Click to show hint 3
    await user.click(screen.getByTestId("show-next-hint"));
    expect(screen.getByText("Hints (3/3)")).toBeInTheDocument();
    expect(screen.getByText(HINT_3)).toBeInTheDocument();

    // Button should be gone when all hints shown
    expect(screen.queryByTestId("show-next-hint")).not.toBeInTheDocument();
  });

  it("collapses and expands individual hints on click", async () => {
    const user = userEvent.setup();
    render(<HintPanel kataId="test-kata" hints={HINTS} />);

    // Show hint 1
    await user.click(screen.getByTestId("show-next-hint"));
    const hintButton = screen.getByTestId("hint-0");
    expect(hintButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText(HINT_1)).toBeInTheDocument();

    // Collapse hint 1
    await user.click(hintButton);
    expect(hintButton).toHaveAttribute("aria-expanded", "false");
  });

  it("persists hint state to localStorage", async () => {
    const user = userEvent.setup();
    render(<HintPanel kataId="test-kata" hints={HINTS} />);

    // Show 2 hints
    await user.click(screen.getByTestId("show-next-hint"));
    await user.click(screen.getByTestId("show-next-hint"));

    const raw = localStorage.getItem("quantum-katas-progress-hints");
    expect(raw).toBeTruthy();
    const parsed = JSON.parse(String(raw)) as Record<string, number>;
    expect(parsed["test-kata"]).toBe(2);
  });

  it("restores hint state from localStorage on mount", () => {
    localStorage.setItem(
      "quantum-katas-progress-hints",
      JSON.stringify({ "test-kata": 2 }),
    );

    render(<HintPanel kataId="test-kata" hints={HINTS} />);

    expect(screen.getByText("Hints (2/3)")).toBeInTheDocument();
    expect(screen.getByText(HINT_1)).toBeInTheDocument();
    expect(screen.getByText(HINT_2)).toBeInTheDocument();
  });

  it("resets visibleCount when kataId changes", async () => {
    const user = userEvent.setup();
    const HINTS_B = ["Hint B-1", "Hint B-2"];

    const { rerender } = render(<HintPanel kataId="kata-a" hints={HINTS} />);

    // Show 2 hints for kata-a
    await user.click(screen.getByTestId("show-next-hint"));
    await user.click(screen.getByTestId("show-next-hint"));
    expect(screen.getByText("Hints (2/3)")).toBeInTheDocument();

    // Switch to kata-b — visibleCount should reset to 0
    rerender(<HintPanel kataId="kata-b" hints={HINTS_B} />);
    expect(screen.getByText("Hints (0/2)")).toBeInTheDocument();
  });

  it("restores persisted count when switching back to a previously viewed kata", async () => {
    const user = userEvent.setup();

    const { rerender } = render(<HintPanel kataId="kata-a" hints={HINTS} />);

    // Show 1 hint for kata-a (persisted to localStorage)
    await user.click(screen.getByTestId("show-next-hint"));
    expect(screen.getByText("Hints (1/3)")).toBeInTheDocument();

    // Switch to kata-b
    rerender(<HintPanel kataId="kata-b" hints={HINTS} />);
    expect(screen.getByText("Hints (0/3)")).toBeInTheDocument();

    // Switch back to kata-a — should restore 1 from localStorage
    rerender(<HintPanel kataId="kata-a" hints={HINTS} />);
    expect(screen.getByText("Hints (1/3)")).toBeInTheDocument();
  });
});
