/**
 * hooks/useApi.ts
 * ===============
 * Generic hook for client-side API calls with loading, error, and data states.
 *
 * Usage:
 *   const { data, loading, error, refetch } = useApi(() => coverageApi.getCoverage());
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, isApiError } from "@/lib/errors";

export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => void;
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  options?: {
    /** Run immediately on mount (default: true) */
    immediate?: boolean;
    /** Dependency array — refetch when these change */
    deps?: unknown[];
  }
): UseApiState<T> {
  const { immediate = true } = options ?? {};
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(immediate);
  const [error, setError] = useState<ApiError | null>(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcherRef.current();
      setData(result);
    } catch (err) {
      if (isApiError(err)) {
        setError(err);
      } else {
        setError(ApiError.network());
      }
    } finally {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (immediate) {
      execute();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [immediate, ...(options?.deps ?? [])]);

  return { data, loading, error, refetch: execute };
}

export default useApi;
