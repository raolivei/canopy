import React from "react";
import { render, screen } from "@testing-library/react";
import {
  BudgetVsActualsChart,
  BudgetVsActualsData,
} from "@/components/charts/BudgetVsActualsChart";

/**
 * Mock recharts
 */
jest.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ data, children }: any) => (
    <div data-testid="bar-chart" data-points={data.length}>{children}</div>
  ),
  Bar: ({ name }: any) => <div data-testid="bar" data-name={name} />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  Cell: () => <div data-testid="cell" />,
}));

/**
 * Mock chart theme utilities
 */
jest.mock("@/utils/chartTheme", () => ({
  CHART_PALETTE: ["#color1", "#color2", "#color3"],
  getTooltipStyle: () => ({}),
  getGridProps: () => ({}),
  getAxisProps: () => ({}),
  isDarkMode: () => false,
}));

describe("BudgetVsActualsChart", () => {
  const mockData: BudgetVsActualsData[] = [
    {
      category: "Groceries",
      budget: 400,
      actual: 450,
      variance: -50,
      variancePct: 12.5,
    },
    {
      category: "Utilities",
      budget: 200,
      actual: 180,
      variance: 20,
      variancePct: -10,
    },
    {
      category: "Entertainment",
      budget: 100,
      actual: 150,
      variance: -50,
      variancePct: 50,
    },
  ];

  it("renders bar chart with data points", () => {
    render(<BudgetVsActualsChart data={mockData} />);

    const chart = screen.getByTestId("bar-chart");
    expect(chart).toBeInTheDocument();
    expect(chart).toHaveAttribute("data-points", "3");
  });

  it("renders two bars per group (budget, actual)", () => {
    render(<BudgetVsActualsChart data={mockData} />);

    const bars = screen.getAllByTestId("bar");
    expect(bars).toHaveLength(2);
    expect(bars[0]).toHaveAttribute("data-name", "Budget");
    expect(bars[1]).toHaveAttribute("data-name", "Actual");
  });

  it("renders chart container with grid and axes", () => {
    render(<BudgetVsActualsChart data={mockData} />);

    expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
    expect(screen.getByTestId("grid")).toBeInTheDocument();
    expect(screen.getAllByTestId("x-axis")).toHaveLength(1);
    expect(screen.getAllByTestId("y-axis")).toHaveLength(1);
  });

  it("renders tooltip and legend", () => {
    render(<BudgetVsActualsChart data={mockData} />);

    expect(screen.getByTestId("tooltip")).toBeInTheDocument();
    expect(screen.getByTestId("legend")).toBeInTheDocument();
  });

  it("accepts custom currency", () => {
    render(<BudgetVsActualsChart data={mockData} currency="USD" />);

    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("handles empty data", () => {
    render(<BudgetVsActualsChart data={[]} />);

    const chart = screen.getByTestId("bar-chart");
    expect(chart).toHaveAttribute("data-points", "0");
  });
});
