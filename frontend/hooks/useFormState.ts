import { useEffect, useCallback } from "react";

/**
 * Hook to persist form state to sessionStorage for recovery on error
 * Automatically saves on every change and recovers on mount
 */
export function useFormState<T>(formKey: string, initialValue: T) {
  const storageKey = `form_${formKey}`;

  // Recover form data from sessionStorage on mount
  const getRecoveredState = useCallback((): T | null => {
    if (typeof window === "undefined") return null;
    try {
      const stored = sessionStorage.getItem(storageKey);
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      console.warn(`Failed to recover form state for ${formKey}:`, e);
      return null;
    }
  }, [formKey, storageKey]);

  // Save form state to sessionStorage
  const saveFormState = useCallback(
    (state: T) => {
      if (typeof window === "undefined") return;
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(state));
      } catch (e) {
        console.warn(`Failed to save form state for ${formKey}:`, e);
      }
    },
    [formKey, storageKey]
  );

  // Clear form state from sessionStorage
  const clearFormState = useCallback(() => {
    if (typeof window === "undefined") return;
    try {
      sessionStorage.removeItem(storageKey);
    } catch (e) {
      console.warn(`Failed to clear form state for ${formKey}:`, e);
    }
  }, [formKey, storageKey]);

  return {
    getRecoveredState,
    saveFormState,
    clearFormState,
  };
}

/**
 * Hook to handle form submission with auto-save and error recovery
 */
export function useFormSubmit<T>(
  formKey: string,
  onSubmit: (data: T) => Promise<void>
) {
  const { saveFormState, clearFormState } = useFormState(formKey, null);

  const handleSubmit = useCallback(
    async (data: T) => {
      // Save form state before submission (for recovery on error)
      saveFormState(data);

      try {
        await onSubmit(data);
        // Clear saved form state on successful submission
        clearFormState();
      } catch (error) {
        // Keep form state saved for recovery (user can retry)
        throw error;
      }
    },
    [onSubmit, saveFormState, clearFormState]
  );

  return { handleSubmit };
}
