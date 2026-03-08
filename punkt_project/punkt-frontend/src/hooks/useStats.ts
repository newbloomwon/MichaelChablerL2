import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';

interface Stats {
    total_logs: string | number;
    ingestion_rate: string | number;
    error_rate: string | number;
    active_sources: string | number;
    trends: {
        total_logs: { value: string; positive: boolean };
        ingestion_rate: { value: string; positive: boolean };
        error_rate: { value: string; positive: boolean };
        active_sources: { value: string; positive: boolean };
    };
}

export const useStats = () => {
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStats = useCallback(async () => {
        try {
            const response = await api.get('/api/stats/overview');
            if (response.data.success) {
                setStats(response.data.data);
                setError(null);
            } else {
                setError(response.data.error?.message || 'Failed to fetch stats');
            }
        } catch (err: any) {
            // If backend is not ready, we might get 404. 
            // For Day 2 MVP with Beatrice still working, we can fallback to mock if needed,
            // but the plan says "displays real data from backend".
            setError(err.message || 'An error occurred while fetching stats');

            // Fallback for demo purposes if backend isn't ready could be here,
            // but let's stick to the plan and try to fetch.
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStats();
        const interval = setInterval(fetchStats, 30000); // 30s refresh
        return () => clearInterval(interval);
    }, [fetchStats]);

    return { stats, loading, error, refresh: fetchStats };
};
