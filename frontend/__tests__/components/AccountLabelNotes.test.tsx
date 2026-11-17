import { render, screen } from "@testing-library/react";
import { AccountLabelNotes } from "@/components/import/AccountLabelNotes";

describe("AccountLabelNotes", () => {
  it("renders nothing when no labels need attention", () => {
    const { container } = render(
      <AccountLabelNotes defaulted={[]} skipped={[]} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("names defaulted and skipped labels", () => {
    render(
      <AccountLabelNotes defaulted={["Wallet CA"]} skipped={["Mystery"]} />,
    );
    expect(
      screen.getByText(/Imported as cash accounts:/).parentElement,
    ).toHaveTextContent("Wallet CA");
    expect(
      screen.getByText(/Skipped accounts:/).parentElement,
    ).toHaveTextContent("Mystery");
  });
});
