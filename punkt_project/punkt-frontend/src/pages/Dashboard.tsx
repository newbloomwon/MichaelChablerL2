import { FC, useMemo } from 'react';
import { BarChart3, Clock, AlertCircle, Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useStats } from '../hooks/useStats';
import { MetricCard } from '../components/dashboard/MetricCard';
import { LiveFeed } from '../components/feed/LiveFeed';
import { TimeSeriesChart } from '../components/charts/TimeSeriesChart';
import { AggregationChart } from '../components/charts/AggregationChart';

export const DashboardPage: FC = () => {
    const { user } = useAuth();
    const { stats, loading, error } = useStats();

    // Mock data for visualizations
    const mockTimeSeries = useMemo(() => Array.from({ length: 24 }, (_, i) => ({
        timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
        INFO: Math.floor(Math.random() * 800) + 200,
        WARN: Math.floor(Math.random() * 100) + 20,
        ERROR: Math.floor(Math.random() * 30),
        DEBUG: Math.floor(Math.random() * 400),
        CRITICAL: Math.floor(Math.random() * 5),
    })), []);

    const mockStats = useMemo(() => [
        { name: 'nginx-access', value: 4500 },
        { name: 'auth-service', value: 2100 },
        { name: 'payment-gw', value: 1200 },
        { name: 'worker-node', value: 800 },
    ], []);

    const metricConfigs = [
        { key: 'total_logs', name: 'Total Logs Today', icon: BarChart3, color: 'text-primary' },
        { key: 'ingestion_rate', name: 'Avg Ingestion Rate', icon: Activity, color: 'text-accent' },
        { key: 'error_rate', name: 'Error Rate', icon: AlertCircle, color: 'text-error' },
        { key: 'active_sources', name: 'Active Sources', icon: Clock, color: 'text-success' },
    ];

    if (error && !stats) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-gray-400">
                <AlertCircle size={48} className="text-error mb-4" />
                <h2 className="text-xl font-semibold text-white">Error loading statistics</h2>
                <p className="mt-2 text-sm">{error}</p>
                <button
                    onClick={() => window.location.reload()}
                    className="mt-6 px-4 py-2 bg-primary rounded-lg text-white font-medium hover:bg-primary/90 transition-colors"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in transition-all duration-700">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-2">
                <div>
                    <h1 className="text-5xl font-marker text-ink -rotate-1 mb-2">
                        System Overview
                    </h1>
                    <p className="text-ink/60 font-typewriter text-lg">
                        Welcome back, <span className="font-bold text-ink bg-accent/30 px-1">{user?.username}</span>.
                        <br />Monitoring <span className="font-bold underline decoration-wavy decoration-error">{user?.tenant_id}</span> fleet status.
                    </p>
                </div>
                <div className="flex items-center gap-3 px-5 py-2.5 glass-panel rounded-2xl border-white/10 group hover:border-success/30 transition-all">
                    <div className="relative">
                        <div className="w-2.5 h-2.5 bg-success rounded-full animate-ping absolute inset-0 opacity-40" />
                        <div className="w-2.5 h-2.5 bg-success rounded-full relative z-10 shadow-[0_0_12px_rgba(16,185,129,0.9)]" />
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-success/80">Live Stream Connected</span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                {metricConfigs.map((config) => {
                    const value = stats ? (stats as any)[config.key] : '---';
                    const trend = stats?.trends ? (stats.trends as any)[config.key] : undefined;

                    return (
                        <MetricCard
                            key={config.key}
                            name={config.name}
                            value={value}
                            icon={config.icon}
                            color={config.color}
                            trend={trend}
                            loading={loading && !stats}
                        />
                    );
                })}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Top Row: Charts */}
                <div className="lg:col-span-2 glass-panel relative">
                    <div className="tape-strip -top-3 left-10 rotate-[-2deg]"></div>
                    <div className="tape-strip -bottom-3 right-10 rotate-[1deg]"></div>
                    <h3 className="text-2xl font-marker mb-4 text-ink">System Traffic</h3>
                    <TimeSeriesChart data={mockTimeSeries} height={300} />
                </div>

                <div className="lg:col-span-1 glass-panel relative">
                    <div className="tape-strip -top-3 right-1/2 rotate-[3deg]"></div>
                    <h3 className="text-2xl font-marker mb-4 text-ink">Top Sources</h3>
                    <AggregationChart data={mockStats} type="bar" title="" height={250} />
                </div>

                {/* Bottom Row: Live Feed */}
                <div className="lg:col-span-3 glass-panel relative h-[500px] flex flex-col">
                    <div className="tape-strip -top-3 left-1/2 -translate-x-1/2 border-l border-r border-dotted border-gray-400"></div>
                    <h3 className="text-2xl font-marker mb-4 text-ink shrink-0">Live Feed</h3>
                    <div className="flex-1 min-h-0">
                        <LiveFeed />
                    </div>
                </div>
            </div>
        </div>
    );
};
