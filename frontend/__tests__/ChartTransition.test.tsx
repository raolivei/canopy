import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import ChartTransition, { AnimatedNumber } from "@/components/ChartTransition";

describe("ChartTransition", () => {
  it("shows skeleton when loading", () => {
    render(
      <ChartTransition
        isLoading={true}
        skeleton={<div>Skeleton</div>}
        chart={<div>Chart</div>}
      />
    );
    expect(screen.getByText("Skeleton")).toBeInTheDocument();
    expect(screen.queryByText("Chart")).not.toBeInTheDocument();
  });

  it("shows chart when not loading", () => {
    render(
      <ChartTransition
        isLoading={false}
        skeleton={<div>Skeleton</div>}
        chart={<div>Chart</div>}
      />
    );
    expect(screen.queryByText("Skeleton")).not.toBeInTheDocument();
    expect(screen.getByText("Chart")).toBeInTheDocument();
  });

  it("transitions from skeleton to chart", async () => {
    const { rerender } = render(
      <ChartTransition
        isLoading={true}
        skeleton={<div>Skeleton</div>}
        chart={<div>Chart</div>}
      />
    );

    expect(screen.getByText("Skeleton")).toBeInTheDocument();

    rerender(
      <ChartTransition
        isLoading={false}
        skeleton={<div>Skeleton</div>}
        chart={<div>Chart</div>}
      />
    );

    // Skeleton should disappear and chart should appear
    await waitFor(
      () => {
        expect(screen.queryByText("Skeleton")).not.toBeInTheDocument();
        expect(screen.getByText("Chart")).toBeInTheDocument();
      },
      { timeout: 1000 }
    );
  });
});

describe("AnimatedNumber", () => {
  it("renders initial value", () => {
    render(<AnimatedNumber value={100} />);
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("animates number changes", async () => {
    const formatter = (v: number) => `$${v.toFixed(2)}`;
    const { rerender } = render(
      <AnimatedNumber value={100} formatter={formatter} />
    );

    rerender(<AnimatedNumber value={150} formatter={formatter} />);

    // Should eventually show the final value
    await waitFor(
      () => {
        expect(screen.getByText("$150.00")).toBeInTheDocument();
      },
      { timeout: 1000 }
    );
  });

  it("uses custom formatter", () => {
    const formatter = (v: number) => `Count: ${Math.round(v)}`;
    render(<AnimatedNumber value={42} formatter={formatter} />);
    expect(screen.getByText("Count: 42")).toBeInTheDocument();
  });
});
