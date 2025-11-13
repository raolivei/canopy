import { useState, useTransition } from 'react';

interface OptimisticUpdateOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export function useOptimisticUpdate<T>(
  updateFn: () => Promise<T>,
  options?: OptimisticUpdateOptions<T>
) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<Error | null>(null);

  const execute = async () => {
    setError(null);
    startTransition(async () => {
      try {
        const result = await updateFn();
        options?.onSuccess?.(result);
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        options?.onError?.(error);
      }
    });
  };

  return {
    execute,
    isPending,
    error,
  };
}

