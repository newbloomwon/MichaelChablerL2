import { useState, useEffect } from 'react';
import { LogEntry } from '../components/feed/LiveFeed';

export const useLiveLogs = () => {
    const [logs, setLogs] = useState<LogEntry[]>([]);

    useEffect(() => {
        // Mock log generation
        const interval = setInterval(() => {
            const newLog: LogEntry = {
                id: Math.random().toString(36).substr(2, 9),
                timestamp: new Date().toISOString(),
                level: ['INFO', 'DEBUG', 'WARN', 'ERROR', 'CRITICAL'][Math.floor(Math.random() * 5)] as any,
                source: ['nginx', 'auth-service', 'db-worker', 'api-gateway'][Math.floor(Math.random() * 4)],
                message: [
                    'GET /api/v1/health 200 OK',
                    'User login attempt from 192.168.1.1',
                    'Database connection latency: 45ms',
                    'Failed to process image chunk #402',
                    'Buffer overflow in worker process',
                    'Incoming request: POST /api/ingest/json',
                    'Cache hit for user session: a9f8e4',
                    'Memory usage at 85% - scaling up'
                ][Math.floor(Math.random() * 8)]
            };

            setLogs(prev => [...prev, newLog].slice(-200)); // Keep last 200 in memory
        }, 1500);

        return () => clearInterval(interval);
    }, []);

    return { logs, clearLogs: () => setLogs([]) };
};
