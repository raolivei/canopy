import React from "react";
import { render, screen } from "@testing-library/react";
import {
  CategoryBreakdown,
  CategoryBreakdownData,
} from "@/components/charts/CategoryBreakdown";

/**
 * Mock recharts
 */
jest.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: any) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: ({ data, children }: any) => (
    <div data-testid="pie" data-points={data.length}>{children}</div>
  ),
  Cell: ({ fill }: any) => (
    <div data-testid="cell" data-fill={fill} />
  ),
  Tooltip: () => <div data-testid="tooltip" />,
}));

/**
 * Mock chart theme utilities
 */
jest.mock("@/utils/chartTheme", () => ({
  CHART_PALETTE: [
    "#color1",
    "#color2",
    "#color3",
    "#color4",
    "#color5",
  ],
  getTooltipStyle: () => ({}),
  isDarkMode: () => false,
}));

describe("CategoryBreakdown", () => {
  const mockData: CategoryBreakdownData[] = [
    { category: "Groceries", amount: 500, pct: 25 },
    { category: "Rent", amount: 1000, pct: 50 },
    { category: "Entertainment", amount: 300, pct: 15 },
    { category: "Other", amount: 200, pct: 10 },
  ];

  it("renders pie chart with data points", () => {
    render(<CategoryBreakdown data={mockData} />);

    const pie = screen.getByTestId("pie");
    expect(pie).toBeInTheDocument();
    expect(pie).toHaveAttribute("data-points", "4");
  });

  it("renders cells for each category", () => {
    render(<CategoryBreakdown data={mockData} />);

    const cells = screen.getAllByTestId("cell");
    expect(cells).toHaveLength(4);
  });

  it("renders legend with categories and amounts", () => {
    render(<CategoryBreakdown data={mockData} />);

    expect(screen.getByText("Groceries")).toBeInTheDocument();
    expect(screen.getByText("Rent")).toBeInTheDocument();
    expect(screen.getByText("Entertainment")).toBeInTheDocument();
  });

  it("hides legend when showLegend is false", () => {
    const { container } = render(
      <CategoryBreakdown data={mockData} showLegend={false} />
    );

    const legendContainer = container.querySelector(
      ".mt-2.space-y-1\\.5"
    );
    expect(legendContainer).not.toBeInTheDocument();
  });

  it("renders tooltip", () => {
    render(<CategoryBreakdown data={mockData} />);

    expect(screen.getByTestId("tooltip")).toBeInTheDocument();
  });

  it("accepts custom currency", () => {
    render(<CategoryBreakdown data={mockData} currency="USD" />);

    expect(screen.getByTestId("pie-chart")).toBeInTheDocument();
  });

  it("accepts custom max legend height", () => {
    const { container } = render(
      <CategoryBreakdown
        data={mockData}
        maxLegendHeight="max-h-80"
      />
    );

    const legend = container.querySelector(".max-h-80");
    expect(legend).toBeInTheDocument();
  });

  it("handles empty data", () => {
    render(<CategoryBreakdown data={[]} />);

    const pie = screen.getByTestId("pie");
    expect(pie).toHaveAttribute("data-points", "0");
  });
});
