import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { LogEntry } from '../components/feed/LiveFeed';

export type ConnectionStatus = 'connecting' | 'open' | 'closing' | 'closed' | 'error';

interface UseWebSocketReturn {
    status: ConnectionStatus;
    lastLog: LogEntry | null;
    error: string | null;
    reconnect: () => void;
}

const RECONNECT_INTERVAL = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

// Helper to determine robust WebSocket URL
const getWebSocketUrl = (path: string) => {
    // 1. Explicit Env Var (if set in .env)
    if (import.meta.env.VITE_WS_URL) return `${import.meta.env.VITE_WS_URL}${path}`;

    // 2. Derived from API Base URL (if set)
    if (import.meta.env.VITE_API_BASE_URL) {
        return `${import.meta.env.VITE_API_BASE_URL.replace('http', 'ws')}${path}`;
    }

    // 3. Dynamic Fallback (best for Docker/Production without env vars)
    // This assumes the API is relative or on the same host at port 8000
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname; // e.g. 'localhost' or '192.168.x.x' or 'my-domain.com'
    const port = '8000'; // Default backend port
    return `${protocol}//${host}:${port}${path}`;
};

export const useWebSocket = (path: string): UseWebSocketReturn => {
    const { token, user } = useAuth();
    const [status, setStatus] = useState<ConnectionStatus>('closed');
    const [lastLog, setLastLog] = useState<LogEntry | null>(null);
    const [error, setError] = useState<string | null>(null);
    const ws = useRef<WebSocket | null>(null);
    const reconnectAttempts = useRef(0);
    const reconnectTimeout = useRef<any>(null);

    const connect = useCallback(() => {
        if (!token || !user?.tenant_id) return;

        // Use robust URL generator
        const baseUrl = getWebSocketUrl(path);
        // Ensure path isn't duplicated if getWebSocketUrl already appended it (it does in my impl above)
        // Actually, my helper appends path. So we just need:
        const url = `${baseUrl}?token=${token}`;

        console.log(`[WS] Connecting to ${url}`);
        setStatus('connecting');

        try {
            ws.current = new WebSocket(url);

            ws.current.onopen = () => {
                console.log('[WS] Connection established');
                setStatus('open');
                setError(null);
                reconnectAttempts.current = 0;
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'ping') {
                        ws.current?.send(JSON.stringify({ type: 'pong' }));
                    } else if (data.type === 'log') {
                        setLastLog(data.payload);
                    } else if (data.type === 'log_batch') {
                        // For batch messages, use the most recent log
                        const logs = Array.isArray(data.payload) ? data.payload : [];
                        if (logs.length > 0) {
                            setLastLog(logs[logs.length - 1]);
                        }
                    }
                } catch (e) {
                    console.error('[WS] Error parsing message:', e);
                }
            };

            ws.current.onclose = (event) => {
                console.log('[WS] Connection closed', event.code, event.reason);
                setStatus('closed');

                // Attempt reconnection if not a clean close
                if (!event.wasClean && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
                    const delay = RECONNECT_INTERVAL * Math.pow(2, reconnectAttempts.current);
                    console.log(`[WS] Reconnecting in ${delay}ms...`);
                    reconnectTimeout.current = setTimeout(() => {
                        reconnectAttempts.current += 1;
                        connect();
                    }, delay);
                }
            };

            ws.current.onerror = (err) => {
                console.error('[WS] Connection error:', err);
                setStatus('error');
                setError('WebSocket connection error');
            };
        } catch (e) {
            console.error('[WS] Exception during connection:', e);
            setStatus('error');
            setError('Failed to initialize WebSocket');
        }
    }, [path, token, user?.tenant_id]);

    const disconnect = useCallback(() => {
        if (ws.current) {
            ws.current.close(1000, 'User navigating away');
            ws.current = null;
        }
        if (reconnectTimeout.current) {
            clearTimeout(reconnectTimeout.current);
        }
    }, []);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        status,
        lastLog,
        error,
        reconnect: () => {
            reconnectAttempts.current = 0;
            connect();
        }
    };
};
