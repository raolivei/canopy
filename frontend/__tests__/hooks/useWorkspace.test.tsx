import { act, renderHook } from "@testing-library/react";

import { useWorkspace, workspaceForPath, workspaceHome, WORKSPACE_STORAGE_KEY, workspaceRequiredByPath } from "@/hooks/useWorkspace";

beforeEach(() => {
  window.localStorage.clear();
});

describe("useWorkspace", () => {
  it("defaults to wallet and hydrates", () => {
    const { result } = renderHook(() => useWorkspace());
    expect(result.current.workspace).toBe("wallet");
    expect(result.current.hydrated).toBe(true);
  });

  it("reads a stored selection and ignores garbage", () => {
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, "tax");
    expect(renderHook(() => useWorkspace()).result.current.workspace).toBe("tax");

    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, "crypto");
    expect(renderHook(() => useWorkspace()).result.current.workspace).toBe("wallet");
  });

  it("persists changes and keeps other consumers in sync", () => {
    const first = renderHook(() => useWorkspace());
    const second = renderHook(() => useWorkspace());

    act(() => first.result.current.setWorkspace("tax"));

    expect(window.localStorage.getItem(WORKSPACE_STORAGE_KEY)).toBe("tax");
    expect(first.result.current.workspace).toBe("tax");
    expect(second.result.current.workspace).toBe("tax");
  });
});

describe("workspaceForPath / workspaceHome", () => {
  it.each([
    ["/", "wallet"],
    ["/budgets", "wallet"],
    ["/taxes", "wallet"],
    ["/tax", "tax"],
    ["/tax/2025", "tax"],
  ])("%s belongs to %s", (path, expected) => {
    expect(workspaceForPath(path)).toBe(expected);
  });

  it.each([
    ["/", "wallet"],
    ["/budgets", "wallet"],
    ["/settings/integrations", "wallet"],
    ["/tax", "tax"],
    ["/tax/2025", "tax"],
    ["/settings", null],
  ])("%s requires %s", (path, expected) => {
    expect(workspaceRequiredByPath(path)).toBe(expected);
  });

  it("knows each workspace's landing route", () => {
    expect(workspaceHome("wallet")).toBe("/");
    expect(workspaceHome("tax")).toBe("/tax");
  });
});
