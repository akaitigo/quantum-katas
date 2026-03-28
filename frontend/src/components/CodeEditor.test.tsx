import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CodeEditor } from "./CodeEditor";

// Mock @monaco-editor/react to avoid loading the actual Monaco Editor in tests
vi.mock("@monaco-editor/react", () => {
  return {
    default: function MockEditor({
      value,
      onChange,
      "data-testid": dataTestId,
    }: {
      readonly value: string;
      readonly onChange?: (value: string | undefined) => void;
      readonly "data-testid"?: string;
    }) {
      return (
        <textarea
          data-testid={dataTestId ?? "monaco-editor-mock"}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          aria-label="Monaco Editor Mock"
        />
      );
    },
  };
});

describe("CodeEditor", () => {
  it("renders the editor wrapper", () => {
    render(<CodeEditor value="import cirq" onChange={() => {}} />);

    expect(screen.getByTestId("code-editor")).toBeInTheDocument();
  });

  it("renders the language label", () => {
    render(<CodeEditor value="import cirq" onChange={() => {}} />);

    expect(screen.getByText("Python (Cirq)")).toBeInTheDocument();
  });

  it("renders the keyboard shortcut hint", () => {
    render(<CodeEditor value="import cirq" onChange={() => {}} />);

    expect(screen.getByText(/Ctrl\+Enter/)).toBeInTheDocument();
  });

  it("renders the mocked editor with the given value", () => {
    render(<CodeEditor value="import cirq" onChange={() => {}} />);

    const textarea = screen.getByLabelText("Monaco Editor Mock");
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveValue("import cirq");
  });
});
