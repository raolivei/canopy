import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import Sidebar from "@/components/layout/Sidebar";
import MobileNav from "@/components/layout/MobileNav";
import { WORKSPACE_STORAGE_KEY } from "@/hooks/useWorkspace";

const push = jest.fn();
let pathname = "/";

jest.mock("next/router", () => ({
  useRouter: () => ({ pathname, push, replace: jest.fn(), query: {} }),
}));

jest.mock("framer-motion", () => {
  const React = require("react");
  const passthrough = (tag: string) =>
    React.forwardRef(function Motion({ children, initial, animate, exit, transition, ...rest }: any, ref: any) {
      return React.createElement(tag, { ...rest, ref }, children);
    });
  return {
    motion: { aside: passthrough("aside"), div: passthrough("div"), span: passthrough("span") },
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

beforeEach(() => {
  window.localStorage.clear();
  push.mockClear();
  pathname = "/";
});

describe("Sidebar workspace switch", () => {
  it("shows the Wallet navigation with Budgets and Cash Flow by default", async () => {
    render(<Sidebar />);

    await waitFor(() => expect(screen.getByRole("group", { name: "Workspace" })).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Wallet" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("link", { name: /Budgets/ })).toHaveAttribute("href", "/budgets");
    expect(screen.getByRole("link", { name: /Cash Flow/ })).toHaveAttribute("href", "/cashflow");
    expect(screen.getByRole("link", { name: /Exchange/ })).toHaveAttribute("href", "/exchange");
    expect(screen.getByRole("link", { name: /Holdings/ })).toBeInTheDocument();
  });

  it("switches to Tax, navigates to /tax and swaps the navigation", async () => {
    render(<Sidebar />);
    await waitFor(() => screen.getByRole("button", { name: "Tax" }));

    fireEvent.click(screen.getByRole("button", { name: "Tax" }));

    expect(push).toHaveBeenCalledWith("/tax");
    expect(window.localStorage.getItem(WORKSPACE_STORAGE_KEY)).toBe("tax");
    expect(screen.getByRole("button", { name: "Tax" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("link", { name: /Tax overview/ })).toHaveAttribute("href", "/tax");
    expect(screen.queryByRole("link", { name: /Holdings/ })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Settings/ })).toBeInTheDocument();
  });

  it("follows a deep link into /tax", async () => {
    pathname = "/tax";
    render(<Sidebar />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Tax" })).toHaveAttribute("aria-pressed", "true"));
    expect(push).not.toHaveBeenCalled();
  });

  it("does not navigate when already inside the chosen workspace", async () => {
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, "tax");
    pathname = "/tax";
    render(<Sidebar />);
    await waitFor(() => screen.getByRole("button", { name: "Wallet" }));

    fireEvent.click(screen.getByRole("button", { name: "Tax" }));
    expect(push).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Wallet" }));
    expect(push).toHaveBeenCalledWith("/");
  });

  it("keeps Wallet selected when leaving Tax through the switch", async () => {
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, "tax");
    pathname = "/tax";
    const { rerender } = render(<Sidebar />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Tax" })).toHaveAttribute("aria-pressed", "true"));

    // The route is still /tax until the navigation lands.
    fireEvent.click(screen.getByRole("button", { name: "Wallet" }));
    expect(push).toHaveBeenCalledWith("/");
    expect(screen.getByRole("button", { name: "Wallet" })).toHaveAttribute("aria-pressed", "true");
    expect(window.localStorage.getItem(WORKSPACE_STORAGE_KEY)).toBe("wallet");

    pathname = "/";
    rerender(<Sidebar />);
    expect(screen.getByRole("button", { name: "Wallet" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("link", { name: /Holdings/ })).toBeInTheDocument();
  });

  it("returns to Wallet on a Wallet page even when Tax was stored", async () => {
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, "tax");
    pathname = "/budgets";
    render(<Sidebar />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Wallet" })).toHaveAttribute("aria-pressed", "true"));
    expect(window.localStorage.getItem(WORKSPACE_STORAGE_KEY)).toBe("wallet");
    expect(push).not.toHaveBeenCalled();
  });

  it("keeps the current workspace on a shared page", async () => {
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, "tax");
    pathname = "/settings";
    render(<Sidebar />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Tax" })).toHaveAttribute("aria-pressed", "true"));
    expect(screen.getByRole("link", { name: /Tax overview/ })).toBeInTheDocument();
  });
});

describe("MobileNav", () => {
  it("renders the Wallet bar unchanged by default and the Tax bar when selected", async () => {
    const { unmount } = render(<MobileNav />);
    await waitFor(() => screen.getByRole("navigation", { name: "Wallet navigation" }));
    expect(screen.getAllByRole("link").map((l) => l.textContent)).toEqual([
      "Home",
      "Import",
      "Holdings",
      "Txns",
      "Accounts",
      "More",
    ]);
    unmount();

    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, "tax");
    pathname = "/tax";
    render(<MobileNav />);
    await waitFor(() => screen.getByRole("navigation", { name: "Tax navigation" }));
    expect(screen.getAllByRole("link").map((l) => l.textContent)).toEqual(["Tax", "More"]);
    expect(screen.getByRole("link", { name: "Tax" })).toHaveAttribute("aria-current", "page");
  });
});
