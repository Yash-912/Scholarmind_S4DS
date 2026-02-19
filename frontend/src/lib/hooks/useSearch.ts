"use client";

import { useState, useCallback } from "react";
import { semanticSearch } from "@/lib/api";
import type { SearchResponse } from "@/lib/types";

export function useSearch() {
    const [results, setResults] = useState<SearchResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const search = useCallback(async (query: string, topK = 10, rerank = true) => {
        if (!query.trim()) return;
        setLoading(true);
        setError(null);
        try {
            const data = await semanticSearch(query, topK, rerank);
            setResults(data);
        } catch (err: any) {
            setError(err.message || "Search failed");
        } finally {
            setLoading(false);
        }
    }, []);

    const clear = useCallback(() => {
        setResults(null);
        setError(null);
    }, []);

    return { results, loading, error, search, clear };
}
