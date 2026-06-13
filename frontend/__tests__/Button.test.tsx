import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { Button } from "@/components/ui/Button";

describe("Button", () => {
  it("renders with text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    render(<Button loading>Click me</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("shows loading text when provided", () => {
    render(
      <Button loading loadingText="Saving...">
        Save
      </Button>
    );
    expect(screen.getByText("Saving...")).toBeInTheDocument();
  });

  it("shows success state", () => {
    render(
      <Button showSuccess successText="Saved ✓">
        Save
      </Button>
    );
    expect(screen.getByText("Saved ✓")).toBeInTheDocument();
  });

  it("auto-dismisses success state after 1s", async () => {
    render(
      <Button showSuccess successText="Saved ✓">
        Save
      </Button>
    );
    expect(screen.getByText("Saved ✓")).toBeInTheDocument();

    // Wait for success state to dismiss
    await waitFor(
      () => {
        expect(screen.getByText("Save")).toBeInTheDocument();
      },
      { timeout: 1500 }
    );
  });

  it("disables when loading", () => {
    const { rerender } = render(<Button loading={false}>Click</Button>);
    expect(screen.getByRole("button")).not.toBeDisabled();

    rerender(<Button loading={true}>Click</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("handles loading and success transition", async () => {
    const { rerender } = render(
      <Button loading={true} loadingText="Saving...">
        Save
      </Button>
    );

    expect(screen.getByText("Saving...")).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeDisabled();

    // Transition to success
    rerender(
      <Button loading={false} showSuccess successText="Saved ✓">
        Save
      </Button>
    );

    expect(screen.getByText("Saved ✓")).toBeInTheDocument();

    // Wait for auto-dismiss
    await waitFor(
      () => {
        expect(screen.getByText("Save")).toBeInTheDocument();
      },
      { timeout: 1500 }
    );
  });
});
