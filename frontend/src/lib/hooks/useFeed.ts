"use client";

import { useState, useEffect, useCallback } from "react";
import { getFeed, updateInterests, addBookmark } from "@/lib/api";

export function useFeed() {
    const [feed, setFeed] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [interests, setInterests] = useState<string[]>([]);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getFeed();
            setFeed(data);
            setInterests(data.interests || []);
        } catch (err) {
            console.error("Feed load failed:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    const addInterest = useCallback(
        async (interest: string) => {
            if (!interest.trim()) return;
            const updated = [...interests, interest.trim()];
            setInterests(updated);
            await updateInterests(updated);
            load();
        },
        [interests, load]
    );

    const removeInterest = useCallback(
        async (idx: number) => {
            const updated = interests.filter((_, i) => i !== idx);
            setInterests(updated);
            await updateInterests(updated);
            load();
        },
        [interests, load]
    );

    const bookmark = useCallback(async (paperId: number) => {
        await addBookmark(paperId);
    }, []);

    return { feed, loading, interests, addInterest, removeInterest, bookmark, refresh: load };
}
