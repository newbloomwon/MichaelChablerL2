import { FC } from 'react';
import { Database, Plus, Search, Activity, Clock, FileJson, Server } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useSources } from '../hooks/useSources';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '../lib/utils';

export const SourcesPage: FC = () => {
    const navigate = useNavigate();
    const { sources, loading, error, refresh } = useSources();

    if (loading && sources.length === 0) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <LoadingSpinner size={40} label="Loading your log sources..." />
            </div>
        );
    }

    if (error && sources.length === 0) {
        return (
            <div className="max-w-2xl mx-auto mt-20">
                <ErrorBanner
                    message="Failed to load sources"
                    details={error}
                    onRetry={refresh}
                />
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                        <Database className="text-primary" />
                        Log Sources
                    </h1>
                    <p className="text-gray-400 mt-1">Manage and monitor all your incoming log streams.</p>
                </div>
                <button
                    onClick={() => navigate('/ingest')}
                    className="flex items-center gap-2 px-6 py-2.5 bg-primary text-white font-bold rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
                >
                    <Plus size={20} />
                    Add Source
                </button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-secondary/50 p-6 rounded-2xl border border-gray-800">
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Total Sources</p>
                    <p className="text-3xl font-bold text-white">{sources.length}</p>
                </div>
                <div className="bg-secondary/50 p-6 rounded-2xl border border-gray-800">
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Active Now</p>
                    <p className="text-3xl font-bold text-success">
                        {sources.filter(s => s.status === 'active').length}
                    </p>
                </div>
                <div className="bg-secondary/50 p-6 rounded-2xl border border-gray-800">
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Total Logs Processed</p>
                    <p className="text-3xl font-bold text-accent">
                        {sources.reduce((acc, s) => acc + s.log_count, 0).toLocaleString()}
                    </p>
                </div>
            </div>

            {/* Sources Table */}
            <div className="bg-secondary rounded-2xl border border-gray-800 shadow-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-white border-b-2 border-ink">
                                <th className="px-6 py-4 text-xs font-typewriter font-bold text-ink uppercase tracking-wider">Source Name</th>
                                <th className="px-6 py-4 text-xs font-typewriter font-bold text-ink uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-xs font-typewriter font-bold text-ink uppercase tracking-wider">Format</th>
                                <th className="px-6 py-4 text-xs font-typewriter font-bold text-ink uppercase tracking-wider text-right">Log Count</th>
                                <th className="px-6 py-4 text-xs font-typewriter font-bold text-ink uppercase tracking-wider text-right">Last Log</th>
                                <th className="px-6 py-4 text-xs font-typewriter font-bold text-ink uppercase tracking-wider text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800/50">
                            {sources.map((source) => (
                                <tr key={source.id} className="group hover:bg-accent/10 transition-colors border-b border-ink/10">
                                    <td className="px-6 py-5">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-white border-2 border-ink group-hover:bg-accent/20 transition-colors">
                                                <Server size={18} className="text-ink" />
                                            </div>
                                            <span className="font-typewriter font-bold text-ink">{source.name}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className={cn(
                                            "inline-flex items-center gap-1.5 px-2.5 py-1 border-2 text-[10px] font-typewriter font-bold uppercase",
                                            source.status === 'active' ? "bg-success/10 border-success text-success" : "bg-gray-100 border-ink/20 text-ink/40"
                                        )}>
                                            <div className={cn(
                                                "w-1.5 h-1.5 rounded-full",
                                                source.status === 'active' ? "bg-success animate-pulse" : "bg-ink/40"
                                            )} />
                                            {source.status}
                                        </div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="flex items-center gap-2 text-ink/60">
                                            {source.format === 'json' ? <FileJson size={14} /> : <Activity size={14} />}
                                            <span className="uppercase text-[10px] font-typewriter font-bold tracking-widest">{source.format}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 text-right font-typewriter font-bold text-ink">
                                        {source.log_count.toLocaleString()}
                                    </td>
                                    <td className="px-6 py-5 text-right text-xs text-ink/60 font-typewriter">
                                        <div className="flex flex-col items-end">
                                            <div className="flex items-center gap-1.5">
                                                <Clock size={12} />
                                                {formatDistanceToNow(new Date(source.last_log_at))} ago
                                            </div>
                                            <span className="text-[10px] opacity-50">{source.last_log_at}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="flex items-center justify-center gap-2">
                                            <button
                                                onClick={() => navigate(`/search?query=source="${source.name}"`)}
                                                className="p-2 bg-white border-2 border-ink hover:bg-accent hover:border-accent transition-all text-ink"
                                                title="Search logs from this source"
                                            >
                                                <Search size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
