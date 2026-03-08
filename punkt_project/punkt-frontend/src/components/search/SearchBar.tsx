import { FC, useState, KeyboardEvent } from 'react';
import { Search, Clock, HelpCircle, Filter, X } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SearchBarProps {
    onSearch: (query: string, timeRange: string) => void;
    isLoading?: boolean;
    initialQuery?: string;
    tookMs?: number;
}

const TIME_PRESETS = [
    { label: '15m', value: '15m' },
    { label: '1h', value: '1h' },
    { label: '24h', value: '24h' },
    { label: '7d', value: '7d' },
    { label: '30d', value: '30d' },
];

const QUERY_EXAMPLES = [
    { q: 'level=ERROR', d: 'Filter by error level' },
    { q: 'source="nginx"', d: 'Filter by log source' },
    { q: '| stats count by source', d: 'Aggregate result counts' },
    { q: 'status=500 message="timeout"', d: 'Implicit AND search' },
];

export const SearchBar: FC<SearchBarProps> = ({ onSearch, isLoading, initialQuery = '', tookMs }) => {
    const [query, setQuery] = useState(initialQuery);
    const [timeRange, setTimeRange] = useState('15m');
    const [showHelp, setShowHelp] = useState(false);

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && !isLoading) {
            onSearch(query, timeRange);
        }
    };

    return (
        <div className="space-y-4">
            <div className="relative group">
                {/* Search Icon */}
                <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-ink/40 group-focus-within:text-ink transition-colors">
                    <Search size={22} />
                </div>

                {/* Main Input */}
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="level=ERROR | stats count by source"
                    className="input-field w-full py-5 pl-14 pr-48 text-lg shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                    disabled={isLoading}
                />

                {/* Right Actions */}
                <div className="absolute inset-y-0 right-5 flex items-center gap-3">
                    {query && (
                        <button
                            onClick={() => setQuery('')}
                            className="p-1.5 text-ink/40 hover:text-ink transition-colors"
                        >
                            <X size={18} />
                        </button>
                    )}

                    <button
                        onClick={() => setShowHelp(!showHelp)}
                        className={cn(
                            "p-1.5 transition-colors",
                            showHelp ? "text-ink bg-accent/30" : "text-ink/40 hover:text-ink"
                        )}
                        title="Search help"
                    >
                        <HelpCircle size={22} />
                    </button>

                    <div className="h-8 w-[2px] bg-ink/20 mx-1" />

                    <button
                        onClick={() => onSearch(query, timeRange)}
                        disabled={isLoading}
                        className="bg-primary hover:bg-primary/90 text-white px-8 py-2.5 rounded-xl font-bold transition-all shadow-lg active:scale-95 disabled:opacity-50 disabled:scale-100"
                    >
                        {isLoading ? '...' : 'Search'}
                    </button>
                </div>

                {/* Help Tooltip */}
                {showHelp && (
                    <div className="absolute top-full left-0 right-0 mt-4 p-6 glass-panel shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] z-50">
                        <h4 className="text-ink font-marker text-xl mb-4 flex items-center gap-2 -rotate-1">
                            <HelpCircle size={18} className="text-ink" />
                            Query Examples
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {QUERY_EXAMPLES.map((ex) => (
                                <div
                                    key={ex.q}
                                    className="p-3 bg-white border-2 border-ink cursor-pointer hover:bg-accent/20 transition-all"
                                    onClick={() => {
                                        setQuery(ex.q);
                                        setShowHelp(false);
                                    }}
                                >
                                    <p className="font-typewriter text-sm text-ink mb-1">{ex.q}</p>
                                    <p className="text-xs text-ink/60 font-typewriter">{ex.d}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Bottom Controls */}
            <div className="flex flex-wrap items-center justify-between gap-4 px-2">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 text-xs font-typewriter font-bold text-ink/60 uppercase tracking-widest bg-white border-2 border-ink px-3 py-1.5">
                        <Clock size={14} />
                        Time Range
                    </div>
                    <div className="flex p-1 bg-white border-2 border-ink">
                        {TIME_PRESETS.map((p) => (
                            <button
                                key={p.value}
                                onClick={() => setTimeRange(p.value)}
                                className={cn(
                                    "px-4 py-1 text-xs font-typewriter font-bold transition-all",
                                    timeRange === p.value
                                        ? "bg-ink text-white"
                                        : "text-ink/60 hover:text-ink hover:bg-accent/20"
                                )}
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                </div>

                {tookMs !== undefined && (
                    <div className="flex items-center gap-2 text-xs font-typewriter text-ink/60">
                        <Filter size={12} />
                        Query executed in {tookMs}ms
                    </div>
                )}
            </div>
        </div>
    );
};
