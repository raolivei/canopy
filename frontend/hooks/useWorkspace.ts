/**
 * Wallet / Tax workspace selection.
 *
 * Canopy is one application with two primary workspaces. The selection is
 * persisted in ``localStorage`` and broadcast with a custom event so the
 * sidebar and mobile navigation stay in sync. Direct navigation to a ``/tax``
 * URL switches the workspace (see ``workspaceForPath``) so deep links work.
 *
 * Initial render always uses ``"wallet"`` (same hydration strategy as
 * ``usePrivacyMode``) — the stored value is read once in ``useEffect``.
 */

import { useCallback, useEffect, useState } from "react";

export type Workspace = "wallet" | "tax";

export const DEFAULT_WORKSPACE: Workspace = "wallet";
export const WORKSPACE_STORAGE_KEY = "canopy.workspace";
const EVENT_NAME = "canopy:workspace-changed";

function isWorkspace(value: unknown): value is Workspace {
  return value === "wallet" || value === "tax";
}

function readStored(): Workspace {
  if (typeof window === "undefined") return DEFAULT_WORKSPACE;
  try {
    const raw = window.localStorage.getItem(WORKSPACE_STORAGE_KEY);
    return isWorkspace(raw) ? raw : DEFAULT_WORKSPACE;
  } catch {
    return DEFAULT_WORKSPACE;
  }
}

/** The workspace a route belongs to. Only ``/tax`` and its children are Tax. */
export function workspaceForPath(pathname: string): Workspace {
  return pathname === "/tax" || pathname.startsWith("/tax/") ? "tax" : "wallet";
}

/** Landing route of a workspace. */
export function workspaceHome(workspace: Workspace): string {
  return workspace === "tax" ? "/tax" : "/";
}

export function useWorkspace(): {
  workspace: Workspace;
  setWorkspace: (next: Workspace) => void;
  hydrated: boolean;
} {
  const [workspace, setWorkspaceState] = useState<Workspace>(DEFAULT_WORKSPACE);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setWorkspaceState(readStored());
    setHydrated(true);

    const onCustom = () => setWorkspaceState(readStored());
    const onStorage = (event: StorageEvent) => {
      if (event.key === WORKSPACE_STORAGE_KEY) setWorkspaceState(readStored());
    };
    window.addEventListener(EVENT_NAME, onCustom);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(EVENT_NAME, onCustom);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const setWorkspace = useCallback((next: Workspace) => {
    setWorkspaceState(next);
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(WORKSPACE_STORAGE_KEY, next);
    } catch {
      // private mode / quota — in-memory selection still works
    }
    window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: { workspace: next } }));
  }, []);

  return { workspace, setWorkspace, hydrated };
}
