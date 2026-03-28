import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ExecutionResult } from "./ExecutionResult";

describe("ExecutionResult", () => {
  it("renders nothing when there are no results and not loading", () => {
    const { container } = render(
      <ExecutionResult
        executionResult={null}
        validationResult={null}
        isExecuting={false}
        isValidating={false}
      />,
    );

    expect(container.firstChild).toBeNull();
  });

  it("renders loading spinner when executing", () => {
    render(
      <ExecutionResult
        executionResult={null}
        validationResult={null}
        isExecuting={true}
        isValidating={false}
      />,
    );

    expect(screen.getByTestId("execution-loading")).toBeInTheDocument();
    expect(screen.getByText("コードを実行中...")).toBeInTheDocument();
  });

  it("renders loading spinner when validating", () => {
    render(
      <ExecutionResult
        executionResult={null}
        validationResult={null}
        isExecuting={false}
        isValidating={true}
      />,
    );

    expect(screen.getByTestId("execution-loading")).toBeInTheDocument();
    expect(screen.getByText("コードを検証中...")).toBeInTheDocument();
  });

  it("renders successful execution result", () => {
    render(
      <ExecutionResult
        executionResult={{
          stdout: "result=0001100",
          stderr: "",
          success: true,
          error: null,
        }}
        validationResult={null}
        isExecuting={false}
        isValidating={false}
      />,
    );

    expect(screen.getByTestId("execution-result")).toBeInTheDocument();
    expect(screen.getByText("実行成功")).toBeInTheDocument();
    expect(screen.getByText("result=0001100")).toBeInTheDocument();
  });

  it("renders failed execution result with error", () => {
    render(
      <ExecutionResult
        executionResult={{
          stdout: "",
          stderr: "NameError: name 'x' is not defined",
          success: false,
          error: "Runtime error",
        }}
        validationResult={null}
        isExecuting={false}
        isValidating={false}
      />,
    );

    expect(screen.getByTestId("execution-result")).toBeInTheDocument();
    expect(screen.getByText("実行エラー")).toBeInTheDocument();
    expect(screen.getByText("Runtime error")).toBeInTheDocument();
    expect(
      screen.getByText("NameError: name 'x' is not defined"),
    ).toBeInTheDocument();
  });

  it("renders passed validation result", () => {
    render(
      <ExecutionResult
        executionResult={null}
        validationResult={{
          passed: true,
          message: "全てのテストに合格しました!",
          stdout: "test output",
          stderr: "",
        }}
        isExecuting={false}
        isValidating={false}
      />,
    );

    expect(screen.getByTestId("validation-result")).toBeInTheDocument();
    expect(screen.getByText("正解!")).toBeInTheDocument();
    expect(screen.getByText("全てのテストに合格しました!")).toBeInTheDocument();
  });

  it("renders failed validation result", () => {
    render(
      <ExecutionResult
        executionResult={null}
        validationResult={{
          passed: false,
          message: "期待される出力と一致しませんでした",
          stdout: "",
          stderr: "assertion failed",
        }}
        isExecuting={false}
        isValidating={false}
      />,
    );

    expect(screen.getByTestId("validation-result")).toBeInTheDocument();
    expect(screen.getByText("不正解")).toBeInTheDocument();
    expect(
      screen.getByText("期待される出力と一致しませんでした"),
    ).toBeInTheDocument();
  });

  it("shows validation result over execution result when both present", () => {
    render(
      <ExecutionResult
        executionResult={{
          stdout: "exec output",
          stderr: "",
          success: true,
          error: null,
        }}
        validationResult={{
          passed: true,
          message: "正解!",
          stdout: "",
          stderr: "",
        }}
        isExecuting={false}
        isValidating={false}
      />,
    );

    expect(screen.getByTestId("validation-result")).toBeInTheDocument();
    expect(screen.queryByTestId("execution-result")).not.toBeInTheDocument();
  });
});
