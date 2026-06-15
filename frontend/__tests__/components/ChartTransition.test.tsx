import React from "react";
import { render, screen } from "@testing-library/react";
import { ChartTransition } from "@/components/ChartTransition";

/**
 * Mock framer-motion to avoid animation timing issues in tests
 */
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => children,
}));

/**
 * Mock SkeletonChart
 */
jest.mock("@/components/ui/Skeleton", () => ({
  SkeletonChart: () => <div data-testid="skeleton-chart">Skeleton Loading</div>,
}));

describe("ChartTransition", () => {
  it("renders skeleton when isLoading is true", () => {
    render(
      <ChartTransition isLoading={true}>
        <div data-testid="chart-content">Chart Data</div>
      </ChartTransition>
    );

    expect(screen.getByTestId("skeleton-chart")).toBeInTheDocument();
    expect(screen.queryByTestId("chart-content")).not.toBeInTheDocument();
  });

  it("renders content when isLoading is false", () => {
    render(
      <ChartTransition isLoading={false}>
        <div data-testid="chart-content">Chart Data</div>
      </ChartTransition>
    );

    expect(screen.getByTestId("chart-content")).toBeInTheDocument();
    expect(screen.queryByTestId("skeleton-chart")).not.toBeInTheDocument();
  });

  it("transitions from skeleton to content", () => {
    const { rerender } = render(
      <ChartTransition isLoading={true}>
        <div data-testid="chart-content">Chart Data</div>
      </ChartTransition>
    );

    expect(screen.getByTestId("skeleton-chart")).toBeInTheDocument();

    rerender(
      <ChartTransition isLoading={false}>
        <div data-testid="chart-content">Chart Data</div>
      </ChartTransition>
    );

    expect(screen.getByTestId("chart-content")).toBeInTheDocument();
  });

});
