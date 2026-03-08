import { FC, useState, useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import {
    ChevronDown,
    ChevronRight,
    Hash,
    Info,
    AlertTriangle,
    XCircle,
    Bug,
    ArrowUpDown
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { LogEntry } from '../feed/LiveFeed';
import { format } from 'date-fns';

interface ResultsTableProps {
    results: LogEntry[];
    isLoading?: boolean;
    totalCount?: number;
}

const LEVEL_CONFIG = {
    DEBUG: { color: 'text-gray-400 bg-gray-400/10', icon: Bug },
    INFO: { color: 'text-blue-400 bg-blue-400/10', icon: Info },
    WARN: { color: 'text-yellow-500 bg-yellow-500/10', icon: AlertTriangle },
    ERROR: { color: 'text-red-500 bg-red-500/10', icon: XCircle },
    CRITICAL: { color: 'text-red-600 bg-red-600/20 font-bold', icon: XCircle },
};

export const ResultsTable: FC<ResultsTableProps> = ({ results, totalCount }) => {
    const parentRef = useRef<HTMLDivElement>(null);
    const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

    const toggleRow = (id: string) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpandedRows(newExpanded);
    };

    const rowVirtualizer = useVirtualizer({
        count: results.length,
        getScrollElement: () => parentRef.current,
        estimateSize: (index) => {
            const id = results[index]?.id;
            return expandedRows.has(id) ? 300 : 52; // Estimate size based on expansion
        },
        overscan: 10,
    });

    return (
        <div className="flex flex-col h-full bg-secondary rounded-2xl border border-gray-800 shadow-2xl overflow-hidden">
            {/* Table Header */}
            <div className="grid grid-cols-[180px_100px_150px_1fr_40px] px-6 py-4 bg-gray-900/50 border-b border-gray-800 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <div className="flex items-center gap-2">
                    Time <ArrowUpDown size={12} />
                </div>
                <div className="flex items-center gap-2">Level</div>
                <div className="flex items-center gap-2">
                    Source <ArrowUpDown size={12} />
                </div>
                <div>Message</div>
                <div></div>
            </div>

            {/* Virtualized List Container */}
            <div
                ref={parentRef}
                className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-800"
                style={{ height: '600px' }}
            >
                <div
                    style={{
                        height: `${rowVirtualizer.getTotalSize()}px`,
                        width: '100%',
                        position: 'relative',
                    }}
                >
                    {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                        const log = results[virtualRow.index];
                        const isExpanded = expandedRows.has(log.id);
                        const Config = LEVEL_CONFIG[log.level];

                        return (
                            <div
                                key={virtualRow.key}
                                data-index={virtualRow.index}
                                ref={rowVirtualizer.measureElement}
                                className={cn(
                                    "absolute top-0 left-0 w-full border-b border-gray-800/50 transition-colors group",
                                    isExpanded ? "bg-gray-900/40" : "hover:bg-gray-800/30"
                                )}
                                style={{
                                    transform: `translateY(${virtualRow.start}px)`,
                                }}
                            >
                                <div className="grid grid-cols-[180px_100px_150px_1fr_40px] px-6 py-4 items-center">
                                    <div className="text-sm text-gray-400 font-mono italic">
                                        {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                                    </div>
                                    <div>
                                        <span className={cn(
                                            "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold tracking-widest uppercase",
                                            Config.color
                                        )}>
                                            <Config.icon size={10} />
                                            {log.level}
                                        </span>
                                    </div>
                                    <div className="text-sm text-gray-300 flex items-center gap-2">
                                        <Hash size={14} className="text-gray-600" />
                                        <span className="truncate max-w-[120px]">{log.source}</span>
                                    </div>
                                    <div className="text-sm text-gray-200 font-mono truncate">
                                        {log.message}
                                    </div>
                                    <button
                                        onClick={() => toggleRow(log.id)}
                                        className="text-gray-600 hover:text-primary transition-colors"
                                    >
                                        {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                                    </button>
                                </div>

                                {isExpanded && (
                                    <div className="px-6 pb-6 pt-2 animate-in slide-in-from-top-2 duration-200">
                                        <div className="bg-gray-950 rounded-xl p-4 border border-gray-800 font-mono text-xs space-y-4">
                                            <div>
                                                <h4 className="text-gray-500 mb-1 uppercase tracking-tighter text-[10px]">Full Message</h4>
                                                <p className="text-gray-200 whitespace-pre-wrap break-all">{log.message}</p>
                                            </div>

                                            {log.metadata && Object.keys(log.metadata).length > 0 && (
                                                <div>
                                                    <h4 className="text-gray-500 mb-2 uppercase tracking-tighter text-[10px]">Metadata</h4>
                                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                        {Object.entries(log.metadata).map(([key, value]) => (
                                                            <div key={key} className="bg-gray-900/50 p-2 rounded border border-gray-800">
                                                                <span className="text-accent block mb-0.5">{key}</span>
                                                                <span className="text-gray-400">{JSON.stringify(value)}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            <div className="pt-2 flex items-center gap-4 text-[10px] text-gray-600">
                                                <span>ID: {log.id}</span>
                                                <span>ISO: {log.timestamp}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-3 bg-gray-900/50 border-t border-gray-800 flex justify-between items-center text-xs text-gray-500 uppercase tracking-widest font-bold">
                <div className="flex items-center gap-4">
                    <span>Showing {results.length} results</span>
                    {totalCount && totalCount > results.length && (
                        <span className="text-gray-700">| Total: {totalCount}</span>
                    )}
                </div>
                <div>
                    TanStack Virtual Active
                </div>
            </div>
        </div>
    );
};
