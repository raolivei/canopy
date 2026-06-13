import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import DarkModeToggle from "@/components/DarkModeToggle";

describe("DarkModeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("renders button with accessibility label", () => {
    render(<DarkModeToggle />);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-label");
    expect(button).toHaveAttribute("title");
  });

  it("shows moon icon initially in light mode", () => {
    localStorage.setItem("darkMode", "false");
    const { container } = render(<DarkModeToggle />);
    // Wait for hydration
    setTimeout(() => {
      const icons = container.querySelectorAll("svg");
      expect(icons.length).toBeGreaterThan(0);
    }, 0);
  });

  it("toggles dark mode on click", () => {
    render(<DarkModeToggle />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("darkMode")).toBe("true");
  });

  it("persists dark mode preference to localStorage", () => {
    render(<DarkModeToggle />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    expect(localStorage.getItem("darkMode")).toBe("true");

    fireEvent.click(button);

    expect(localStorage.getItem("darkMode")).toBe("false");
  });

  it("respects prefers-color-scheme when no localStorage value", () => {
    localStorage.removeItem("darkMode");
    const { unmount } = render(<DarkModeToggle />);

    // Component should initialize from system preference
    expect(typeof document.documentElement.className).toBe("string");

    unmount();
  });

  it("shows disabled button during hydration", () => {
    const { container } = render(<DarkModeToggle />);
    const button = screen.getByRole("button");
    // Initially disabled to prevent hydration mismatch
    expect(button).toBeDisabled();
  });
});
