import { FC, useState, useEffect, useCallback } from 'react';
import { Download, LayoutDashboard, Share2 } from 'lucide-react';
import { SearchBar } from '../components/search/SearchBar';
import { ResultsTable } from '../components/search/ResultsTable';
import { TimeSeriesChart } from '../components/charts/TimeSeriesChart';
import { AggregationChart } from '../components/charts/AggregationChart';
import api from '../lib/api';
import { LogEntry } from '../components/feed/LiveFeed';
import { convertToCSV, downloadCSV } from '../utils/export';
import { useToast } from '../context/ToastContext';

export const SearchPage: FC = () => {
    const { showToast } = useToast();
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<LogEntry[]>([]);
    const [stats, setStats] = useState<any[]>([]);
    const [timeSeries, setTimeSeries] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [tookMs, setTookMs] = useState<number>();
    const [error, setError] = useState<string | null>(null);

    const handleExport = () => {
        if (results.length === 0) {
            showToast('No results to export', 'warning');
            return;
        }
        try {
            const csv = convertToCSV(results);
            const filename = `punkt_export_${new Date().toISOString().split('T')[0]}.csv`;
            downloadCSV(csv, filename);
            showToast('Export successful', 'success');
        } catch (err) {
            showToast('Export failed', 'error');
        }
    };

    const handleSearch = useCallback(async (searchQuery: string, timeRange: string) => {
        setIsLoading(true);
        setError(null);
        setQuery(searchQuery);

        const startTime = performance.now();

        try {
            const response = await api.get('/api/search', {
                params: {
                    q: searchQuery,
                    time_range: timeRange
                }
            });

            if (response.data.success) {
                // Map backend keys → frontend state
                const data = response.data.data;

                // Backend returns "rows" with {id, timestamp, level, source, message, metadata}
                // Convert epoch timestamps to ISO strings for date-fns compatibility
                const mappedResults = (data.rows || []).map((row: any) => ({
                    ...row,
                    id: String(row.id),
                    timestamp: typeof row.timestamp === 'number'
                        ? new Date(row.timestamp * 1000).toISOString()
                        : row.timestamp,
                }));
                setResults(mappedResults);

                // Backend returns "aggregations" with {source, count} or similar
                // Map to {name, value} shape for AggregationChart
                const mappedStats = (data.aggregations || []).map((agg: any) => ({
                    name: agg.source || agg.level || Object.values(agg)[0],
                    value: agg.count || agg.sum || agg.avg || Object.values(agg)[1] || 0,
                }));
                setStats(mappedStats);

                setTimeSeries(data.time_series || []);
                setTookMs(Math.round(performance.now() - startTime));
            } else {
                throw new Error(response.data.error?.message || 'Search failed');
            }
        } catch (err: any) {
            console.error('Search error:', err);
            // FALLBACK FOR DEMO: If backend is not ready, generate realistic mock data
            generateMockResults(searchQuery);
            setError('Backend search API not fully connected - using mock data for demo');
            setTookMs(Math.round(performance.now() - startTime));
        } finally {
            setIsLoading(false);
        }
    }, []);

    const generateMockResults = (q: string) => {
        const levels: ('INFO' | 'WARN' | 'ERROR' | 'DEBUG' | 'CRITICAL')[] = ['INFO', 'WARN', 'ERROR', 'DEBUG', 'CRITICAL'];
        const mockLogs: LogEntry[] = Array.from({ length: 100 }, (_, i) => ({
            id: `mock-${i}`,
            timestamp: new Date(Date.now() - i * 60000).toISOString(),
            level: levels[Math.floor(Math.random() * levels.length)],
            source: ['nginx', 'auth-service', 'worker-1', 'api-gateway'][Math.floor(Math.random() * 4)],
            message: `Mock log message for query: ${q || 'all'} - Processed internal event ID ${Math.random().toString(36).substr(2, 9)}`,
            metadata: { request_id: 'req-' + i, duration_ms: Math.floor(Math.random() * 500) }
        }));
        setResults(mockLogs);

        const mockStats = [
            { name: 'nginx', value: 45 },
            { name: 'auth-service', value: 25 },
            { name: 'worker-1', value: 20 },
            { name: 'api-gateway', value: 10 },
        ];
        setStats(mockStats);

        const mockTS = Array.from({ length: 24 }, (_, i) => ({
            timestamp: new Date(Date.now() - (24 - i) * 3600000).toISOString(),
            INFO: Math.floor(Math.random() * 1000),
            WARN: Math.floor(Math.random() * 200),
            ERROR: Math.floor(Math.random() * 50),
            DEBUG: Math.floor(Math.random() * 500),
            CRITICAL: Math.floor(Math.random() * 10),
        }));
        setTimeSeries(mockTS);
    };

    // Initial search
    useEffect(() => {
        handleSearch('', '15m');
    }, [handleSearch]);

    const isAggregationQuery = query.toLowerCase().includes('| stats');

    return (
        <div className="space-y-6 animate-in fade-in transition-all duration-700">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                        <LayoutDashboard className="text-primary" />
                        Log Explorer
                    </h1>
                    <p className="text-gray-400 mt-1">Sift through millions of logs with high-performance queries.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => showToast('Sharing feature is coming soon!', 'info')}
                        className="flex items-center gap-2 px-4 py-2 bg-secondary border border-gray-800 rounded-xl text-sm font-bold text-gray-400 hover:text-white hover:border-gray-700 transition-all"
                    >
                        <Share2 size={16} />
                        Share
                    </button>
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl text-sm font-bold shadow-lg shadow-primary/20 hover:scale-[1.02] transition-all"
                    >
                        <Download size={16} />
                        Export Results
                    </button>
                </div>
            </div>

            {/* Search Controls */}
            <div className="bg-secondary/30 p-1 rounded-3xl border border-gray-800">
                <SearchBar
                    onSearch={handleSearch}
                    isLoading={isLoading}
                    tookMs={tookMs}
                />
            </div>

            {error && (
                <div className="flex items-center justify-center p-3 bg-accent/10 border border-accent/20 rounded-xl text-accent text-xs font-medium">
                    {error}
                </div>
            )}

            {/* Visualization Row (Conditional) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <TimeSeriesChart data={timeSeries} height={250} />
                </div>
                <div>
                    <AggregationChart
                        data={stats}
                        type={query.includes('count by') ? 'pie' : 'bar'}
                        title={isAggregationQuery ? "Aggregation Result" : "Top Sources"}
                        height={250}
                    />
                </div>
            </div>

            {/* Results Table */}
            <div className="min-h-[500px]">
                <ResultsTable
                    results={results}
                    isLoading={isLoading}
                    totalCount={12500} // Mock total for demo
                />
            </div>
        </div>
    );
};
