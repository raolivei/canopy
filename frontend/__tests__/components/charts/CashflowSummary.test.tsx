import React from "react";
import { render, screen } from "@testing-library/react";
import {
  CashflowSummary,
  CashflowSummaryData,
} from "@/components/charts/CashflowSummary";

/**
 * Mock recharts
 */
jest.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  ComposedChart: ({ data, children }: any) => (
    <div data-testid="composed-chart" data-points={data.length}>{children}</div>
  ),
  Area: ({ name }: any) => <div data-testid="area" data-name={name} />,
  Line: ({ name }: any) => <div data-testid="line" data-name={name} />,
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
  CHART_PALETTE: ["#color1", "#color2", "#color3", "#color4", "#color5"],
  CHART_COLORS: {
    primary: "#primary",
    success: "#success",
    danger: "#danger",
    accent: "#accent",
  },
  getTooltipStyle: () => ({}),
  getGridProps: () => ({}),
  getAxisProps: () => ({}),
  isDarkMode: () => false,
}));

describe("CashflowSummary", () => {
  const mockData: CashflowSummaryData[] = [
    {
      date: "Jan",
      income: 5000,
      expenses: 3000,
      net: 2000,
      cumulative: 2000,
    },
    {
      date: "Feb",
      income: 5000,
      expenses: 3500,
      net: 1500,
      cumulative: 3500,
    },
    {
      date: "Mar",
      income: 5500,
      expenses: 3000,
      net: 2500,
      cumulative: 6000,
    },
  ];

  it("renders composed chart with data points", () => {
    render(<CashflowSummary data={mockData} />);

    const chart = screen.getByTestId("composed-chart");
    expect(chart).toBeInTheDocument();
    expect(chart).toHaveAttribute("data-points", "3");
  });

  it("renders two areas (income, expenses)", () => {
    render(<CashflowSummary data={mockData} />);

    const areas = screen.getAllByTestId("area");
    expect(areas).toHaveLength(2);
    expect(areas[0]).toHaveAttribute("data-name", "Income");
    expect(areas[1]).toHaveAttribute("data-name", "Expenses");
  });

  it("renders two lines (net, cumulative)", () => {
    render(<CashflowSummary data={mockData} />);

    const lines = screen.getAllByTestId("line");
    expect(lines).toHaveLength(2);
    expect(lines[0]).toHaveAttribute("data-name", "Net");
    expect(lines[1]).toHaveAttribute("data-name", "Cumulative");
  });

  it("renders chart container with grid and axes", () => {
    render(<CashflowSummary data={mockData} />);

    expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
    expect(screen.getByTestId("grid")).toBeInTheDocument();
    expect(screen.getAllByTestId("x-axis")).toHaveLength(1);
    expect(screen.getAllByTestId("y-axis")).toHaveLength(2); // left and right
  });

  it("renders tooltip and legend", () => {
    render(<CashflowSummary data={mockData} />);

    expect(screen.getByTestId("tooltip")).toBeInTheDocument();
    expect(screen.getByTestId("legend")).toBeInTheDocument();
  });

  it("accepts custom currency", () => {
    render(<CashflowSummary data={mockData} currency="USD" />);

    expect(screen.getByTestId("composed-chart")).toBeInTheDocument();
  });

  it("handles empty data", () => {
    render(<CashflowSummary data={[]} />);

    const chart = screen.getByTestId("composed-chart");
    expect(chart).toHaveAttribute("data-points", "0");
  });
});
