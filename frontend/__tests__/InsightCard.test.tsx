import React from "react";
import { render, screen } from "@testing-library/react";
import { InsightCard } from "@/components/ui/InsightCard";

describe("InsightCard", () => {
  it("renders with title and message", () => {
    render(
      <InsightCard
        title="High Spending"
        type="warning"
        metric="78%"
        metricLabel="of budget used"
        description="Groceries spending is above average"
        subtext="C$1,500 / C$2,000"
      />
    );

    expect(screen.getByText("High Spending")).toBeInTheDocument();
    expect(screen.getByText("Groceries spending is above average")).toBeInTheDocument();
    expect(screen.getByText("78%")).toBeInTheDocument();
  });

  it("renders with different types", () => {
    const { rerender } = render(
      <InsightCard title="Test" type="success" metric="✓" />
    );
    expect(screen.getByText("Test")).toBeInTheDocument();

    rerender(<InsightCard title="Test" type="warning" metric="!" />);
    expect(screen.getByText("Test")).toBeInTheDocument();

    rerender(<InsightCard title="Test" type="info" metric="i" />);
    expect(screen.getByText("Test")).toBeInTheDocument();
  });

  it("renders action button when provided", () => {
    const mockAction = jest.fn();
    render(
      <InsightCard
        title="Test"
        type="info"
        action={{
          label: "View Details",
          onClick: mockAction,
        }}
      />
    );

    const button = screen.getByText("View Details");
    expect(button).toBeInTheDocument();
    button.click();
    expect(mockAction).toHaveBeenCalled();
  });

  it("does not render action button when not provided", () => {
    render(<InsightCard title="Test" type="neutral" />);
    expect(screen.queryByText("View Details")).not.toBeInTheDocument();
  });
});
