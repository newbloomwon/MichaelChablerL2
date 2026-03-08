import { FC, useState, useEffect, useRef, useCallback } from 'react';
import { Pause, Play, Terminal, Layers, Trash2, Wifi, WifiOff, AlertTriangle, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { format } from 'date-fns';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAuth } from '../../context/AuthContext';

export interface LogEntry {
    id: string;
    timestamp: string;
    level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
    source: string;
    message: string;
    metadata?: Record<string, any>;
}

interface LiveFeedProps {
    onClear?: () => void;
}

const LEVEL_COLORS = {
    DEBUG: 'text-gray-500',
    INFO: 'text-blue-400',
    WARN: 'text-yellow-500',
    ERROR: 'text-red-500',
    CRITICAL: 'text-red-600 font-bold bg-red-500/10 px-1 rounded',
};

const LEVEL_BG = {
    DEBUG: 'bg-gray-500/5',
    INFO: 'bg-blue-500/5',
    WARN: 'bg-yellow-500/5',
    ERROR: 'bg-red-500/5',
    CRITICAL: 'bg-red-600/10',
};

const LEVEL_BORDER = {
    DEBUG: 'border-l-gray-500',
    INFO: 'border-l-blue-400',
    WARN: 'border-l-yellow-500',
    ERROR: 'border-l-red-500',
    CRITICAL: 'border-l-red-600',
};

const LEVEL_ABBR: Record<LogEntry['level'], string> = {
    DEBUG: 'DBG',
    INFO: 'INF',
    WARN: 'WRN',
    ERROR: 'ERR',
    CRITICAL: 'CRT',
};

export const LiveFeed: FC<LiveFeedProps> = ({ onClear }) => {
    const { user } = useAuth();
    const [isPaused, setIsPaused] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [bufferedLogs, setBufferedLogs] = useState<LogEntry[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);

    // Integrate real-time WebSocket
    const { status, lastLog } = useWebSocket(`/ws/${user?.tenant_id}`);

    // Push new logs to buffer
    useEffect(() => {
        if (lastLog) {
            if (isPaused) {
                setUnreadCount(prev => prev + 1);
            }
            setBufferedLogs(prev => {
                const updated = [...prev, lastLog];
                return updated.slice(-100); // Max 100 logs in memory
            });
        }
    }, [lastLog, isPaused]);

    // Auto-scroll
    useEffect(() => {
        if (!isPaused && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [bufferedLogs, isPaused]);

    const handleTogglePause = useCallback(() => {
        if (isPaused) {
            setUnreadCount(0);
        }
        setIsPaused(!isPaused);
    }, [isPaused]);

    const handleClear = useCallback(() => {
        setBufferedLogs([]);
        setUnreadCount(0);
        if (onClear) onClear();
    }, [onClear]);

    return (
        <div className="flex flex-col h-full bg-[#1a1a1a] border-2 border-ink shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] overflow-hidden font-typewriter text-xs relative">
            {/* Header / Controls */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#2a2a2a] border-b-2 border-ink">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-white border border-ink shadow-[2px_2px_0px_0px_rgba(255,255,255,0.2)]">
                        <Terminal size={16} className="text-ink" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-marker">Stream</h3>
                            <div
                                className={cn(
                                    "flex items-center p-1 border border-white/20",
                                    status === 'open' ? "text-success bg-success/10" : "text-error bg-error/10"
                                )}
                                title={status}
                            >
                                {status === 'open' ? <Wifi size={10} /> : <WifiOff size={10} />}
                            </div>
                        </div>
                        <p className="text-[10px] text-gray-400 flex items-center gap-1">
                            <Layers size={10} />
                            {bufferedLogs.length} buffered
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleClear}
                        className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-all"
                        title="Clear logs"
                    >
                        <Trash2 size={16} />
                    </button>
                    <button
                        onClick={handleTogglePause}
                        className={cn(
                            "flex items-center gap-2 px-3 lg:px-4 py-2 rounded-lg font-bold transition-all",
                            isPaused
                                ? "bg-accent text-white shadow-lg shadow-accent/20"
                                : "bg-gray-800 text-gray-400 hover:text-white"
                        )}
                        title={isPaused ? 'Resume' : 'Pause'}
                    >
                        {isPaused ? <Play size={16} fill="white" /> : <Pause size={16} />}
                        <span className="hidden lg:inline">{isPaused ? 'Resume' : 'Pause'}</span>
                    </button>
                </div>
            </div>

            {/* Logs List */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-1 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent"
            >
                {bufferedLogs.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-500 font-marker gap-2">
                        {status === 'open' ? (
                            <>
                                <Loader2 className="animate-spin" size={24} />
                                <span className="text-lg">Waiting for signal...</span>
                            </>
                        ) : (
                            <>
                                <WifiOff size={24} />
                                <span className="text-lg animate-pulse text-error">NO SIGNAL</span>
                            </>
                        )}
                    </div>
                ) : (
                    bufferedLogs.map((log) => (
                        <div
                            key={log.id}
                            className={cn(
                                "group py-2 px-3 rounded hover:bg-white/5 transition-colors border-l-2",
                                LEVEL_BG[log.level],
                                LEVEL_BORDER[log.level]
                            )}
                        >
                            <div className="flex items-start gap-2 min-w-0">
                                <span className="text-gray-600 shrink-0 select-none font-mono text-[11px]">
                                    {format(new Date(log.timestamp), 'HH:mm:ss')}
                                </span>
                                <span className={cn("w-8 shrink-0 font-bold select-none text-[11px]", LEVEL_COLORS[log.level])}>
                                    {LEVEL_ABBR[log.level]}
                                </span>
                                <span className="text-accent underline decoration-accent/20 shrink-0 select-none text-[11px] max-w-[64px] truncate">
                                    {log.source}
                                </span>
                                <span className="text-gray-300 break-all flex-1 min-w-0 text-[11px]">
                                    {log.message}
                                </span>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Notifications */}
            {isPaused && unreadCount > 0 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-accent px-4 py-2 rounded-full text-white text-[10px] font-bold shadow-2xl animate-bounce flex items-center gap-2">
                    <AlertTriangle size={12} />
                    {unreadCount} new logs buffered
                </div>
            )}

            {/* Backpressure Hint */}
            {bufferedLogs.length >= 95 && (
                <div className="absolute top-20 right-4 p-2 bg-error/10 border border-error/20 rounded-lg text-error text-[10px] animate-pulse flex items-center gap-2">
                    <AlertTriangle size={12} />
                    High Load: Buffer near capacity
                </div>
            )}
        </div>
    );
};
