"use client";

import { useState, useEffect, useCallback } from "react";
import { getDashboard, getQueryAnalytics, getModels } from "@/lib/api";
import { THEME } from "@/lib/constants";
import type { DashboardData } from "@/lib/types";

export function useMetrics() {
    const [dashboard, setDashboard] = useState<DashboardData | null>(null);
    const [analytics, setAnalytics] = useState<Record<string, unknown> | null>(null);
    const [models, setModels] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(true);

    const load = useCallback(async () => {
        try {
            const [dash, anal, mdls] = await Promise.all([
                getDashboard().catch(() => null),
                getQueryAnalytics().catch(() => null),
                getModels().catch(() => null),
            ]);
            setDashboard(dash);
            setAnalytics(anal);
            setModels(mdls);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
        const interval = setInterval(load, THEME.refreshInterval);
        return () => clearInterval(interval);
    }, [load]);

    return { dashboard, analytics, models, loading, refresh: load };
}
