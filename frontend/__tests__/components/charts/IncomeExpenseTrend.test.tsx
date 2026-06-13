import React from "react";
import { render, screen } from "@testing-library/react";
import {
  IncomeExpenseTrend,
  IncomeExpenseTrendData,
} from "@/components/charts/IncomeExpenseTrend";

/**
 * Mock recharts to avoid complex chart rendering in tests
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

describe("IncomeExpenseTrend", () => {
  const mockData: IncomeExpenseTrendData[] = [
    {
      month: 1,
      month_name: "January",
      income: 5000,
      expenses: 3000,
      investments: 1000,
      net: 1000,
    },
    {
      month: 2,
      month_name: "February",
      income: 5000,
      expenses: 3500,
      investments: 1000,
      net: 500,
    },
    {
      month: 3,
      month_name: "March",
      income: 5500,
      expenses: 3000,
      investments: 1500,
      net: 1000,
    },
  ];

  it("renders bar chart with data points", () => {
    render(<IncomeExpenseTrend data={mockData} />);

    const chart = screen.getByTestId("bar-chart");
    expect(chart).toBeInTheDocument();
    expect(chart).toHaveAttribute("data-points", "3");
  });

  it("renders three bars (income, expenses, investments)", () => {
    render(<IncomeExpenseTrend data={mockData} />);

    const bars = screen.getAllByTestId("bar");
    expect(bars).toHaveLength(3);
    expect(bars[0]).toHaveAttribute("data-name", "Income");
    expect(bars[1]).toHaveAttribute("data-name", "Spending");
    expect(bars[2]).toHaveAttribute("data-name", "Invested");
  });

  it("renders chart container with grid and axes", () => {
    render(<IncomeExpenseTrend data={mockData} />);

    expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
    expect(screen.getByTestId("grid")).toBeInTheDocument();
    expect(screen.getAllByTestId("x-axis")).toHaveLength(1);
    expect(screen.getAllByTestId("y-axis")).toHaveLength(1);
  });

  it("renders tooltip and legend", () => {
    render(<IncomeExpenseTrend data={mockData} />);

    expect(screen.getByTestId("tooltip")).toBeInTheDocument();
    expect(screen.getByTestId("legend")).toBeInTheDocument();
  });

  it("accepts custom currency", () => {
    render(<IncomeExpenseTrend data={mockData} currency="USD" />);

    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("handles empty data", () => {
    render(<IncomeExpenseTrend data={[]} />);

    const chart = screen.getByTestId("bar-chart");
    expect(chart).toHaveAttribute("data-points", "0");
  });
});
