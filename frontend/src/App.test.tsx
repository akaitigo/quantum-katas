import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("should be defined", () => {
    expect(App).toBeDefined();
  });

  it("renders the app header", () => {
    render(<App />);
    expect(screen.getByText("uantum Katas")).toBeInTheDocument();
  });
});
