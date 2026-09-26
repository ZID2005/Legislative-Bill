/**
 * hooks/useSearch.ts
 * ==================
 * Hook for the global search (Cmd+K) feature.
 * Debounces queries and calls GET /api/v1/search.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { searchApi } from "@/lib/api/search";
import { isApiError } from "@/lib/errors";
import type { SearchResponse } from "@/types/api";

const DEBOUNCE_MS = 300;

export function useSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const search = useCallback((q: string) => {
    setQuery(q);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (!q.trim()) {
      setResults(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const response = await searchApi.globalSearch(q.trim(), 20);
        setResults(response);
        setError(null);
      } catch (err) {
        if (isApiError(err)) {
          setError(err.userMessage);
        } else {
          setError("Search failed. Please try again.");
        }
        setResults(null);
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);
  }, []);

  const clearSearch = useCallback(() => {
    setQuery("");
    setResults(null);
    setError(null);
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return { query, results, loading, error, search, clearSearch };
}

export default useSearch;
