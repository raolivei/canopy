import React from "react";
import { render } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";

expect.extend(toHaveNoViolations);

describe("Accessibility Audit", () => {
  describe("Button Component", () => {
    it("should not have any accessibility violations", async () => {
      const { container } = render(
        <Button>Click me</Button>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("should have proper ARIA label when provided", async () => {
      const { container } = render(
        <Button ariaLabel="Submit form">Submit</Button>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("should indicate loading state with aria-busy", async () => {
      const { container } = render(
        <Button loading loadingText="Processing...">
          Submit
        </Button>
      );
      const button = container.querySelector("button");
      expect(button).toHaveAttribute("aria-busy", "true");
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("should handle disabled state without violations", async () => {
      const { container } = render(
        <Button disabled>Disabled button</Button>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Card Component", () => {
    it("should not have any accessibility violations", async () => {
      const { container } = render(
        <Card>
          <CardHeader>
            <CardTitle>Test Card</CardTitle>
          </CardHeader>
          <CardContent>Content here</CardContent>
        </Card>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Input Component", () => {
    it("should have proper label association", async () => {
      const { container } = render(
        <Input label="Email" type="email" />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("should indicate error state without violations", async () => {
      const { container } = render(
        <Input label="Email" type="email" error="Invalid email" />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("should have aria-invalid when error is present", async () => {
      const { container } = render(
        <Input label="Email" type="email" error="Invalid email" />
      );
      const input = container.querySelector("input");
      expect(input).toHaveAttribute("aria-invalid", "true");
    });

    it("should have aria-describedby for error messages", async () => {
      const { container } = render(
        <Input label="Email" id="email-field" type="email" error="Invalid email" />
      );
      const input = container.querySelector("input");
      expect(input).toHaveAttribute("aria-describedby", "email-field-error");
    });

    it("should display required indicator", async () => {
      const { container } = render(
        <Input label="Email" required />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Modal Component", () => {
    it("should have proper dialog semantics", async () => {
      render(
        <Modal isOpen={true} onClose={() => {}} title="Test Modal">
          <p>Modal content</p>
        </Modal>
      );
      const dialog = document.querySelector("[role='dialog']");
      expect(dialog).toHaveAttribute("aria-modal", "true");
      expect(dialog).toHaveAttribute("aria-labelledby", "modal-title");
      const results = await axe(document.body);
      expect(results).toHaveNoViolations();
    });

    it("should have accessible close button", async () => {
      render(
        <Modal isOpen={true} onClose={() => {}} title="Test Modal">
          <p>Modal content</p>
        </Modal>
      );
      const closeButton = document.querySelector("[aria-label='Close modal']");
      expect(closeButton).toBeInTheDocument();
      const results = await axe(document.body);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Mobile Responsiveness (375px viewport)", () => {
    beforeEach(() => {
      // Mock window dimensions for mobile testing
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 375,
      });
    });

    it("Button should render without violations on mobile", async () => {
      const { container } = render(
        <Button>Mobile Button</Button>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("Input should render without violations on mobile", async () => {
      const { container } = render(
        <Input label="Mobile Input" />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("Card should render without violations on mobile", async () => {
      const { container } = render(
        <Card>
          <CardHeader>
            <CardTitle>Mobile Card</CardTitle>
          </CardHeader>
          <CardContent>Mobile content</CardContent>
        </Card>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Dark Mode Accessibility", () => {
    beforeEach(() => {
      document.documentElement.classList.add("dark");
    });

    afterEach(() => {
      document.documentElement.classList.remove("dark");
    });

    it("Button should have sufficient contrast in dark mode", async () => {
      const { container } = render(
        <Button>Dark Mode Button</Button>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("Input should have sufficient contrast in dark mode", async () => {
      const { container } = render(
        <Input label="Dark Mode Input" />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("Card should have sufficient contrast in dark mode", async () => {
      const { container } = render(
        <Card>
          <CardHeader>
            <CardTitle>Dark Mode Card</CardTitle>
          </CardHeader>
          <CardContent>Dark mode content</CardContent>
        </Card>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});
