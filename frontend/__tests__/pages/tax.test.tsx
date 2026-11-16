import React from "react";
import { render, screen } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";

import { TaxOverview } from "@/components/tax/TaxOverview";

expect.extend(toHaveNoViolations);

describe("TaxOverview", () => {
  it("states plainly that the workspace is not available and shows no figures", () => {
    render(<TaxOverview />);

    expect(screen.getByText("The Tax workspace is not available yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Wallet" })).toHaveAttribute("href", "/");
    expect(screen.getByText("Document vault")).toBeInTheDocument();
    // No currency amounts or percentages anywhere on a placeholder page.
    expect(document.body.textContent).not.toMatch(/\$\s?\d|\d%/);
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<TaxOverview />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
