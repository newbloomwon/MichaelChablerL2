import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';

export interface Source {
    id: string;
    name: string;
    log_count: number;
    last_log_at: string;
    status: 'active' | 'inactive';
    format: 'json' | 'nginx';
}

export const useSources = () => {
    const [sources, setSources] = useState<Source[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchSources = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.get('/api/sources');
            if (response.data.success) {
                setSources(response.data.data);
                setError(null);
            } else {
                setError(response.data.error?.message || 'Failed to fetch sources');
            }
        } catch (err: any) {
            // Mock fallback if API not ready
            const mockSources: Source[] = [
                { id: '1', name: 'nginx-access', log_count: 45203, last_log_at: new Date().toISOString(), status: 'active', format: 'nginx' },
                { id: '2', name: 'auth-service', log_count: 12400, last_log_at: new Date(Date.now() - 300000).toISOString(), status: 'active', format: 'json' },
                { id: '3', name: 'payment-gateway', log_count: 8900, last_log_at: new Date(Date.now() - 3600000).toISOString(), status: 'active', format: 'json' },
                { id: '4', name: 'legacy-worker', log_count: 500, last_log_at: new Date(Date.now() - 86400000).toISOString(), status: 'inactive', format: 'json' },
            ];
            setSources(mockSources);
            setError(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSources();
    }, [fetchSources]);

    return { sources, loading, error, refresh: fetchSources };
};
