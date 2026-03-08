import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../context/AuthContext';

// Mock useAuth
vi.mock('../context/AuthContext');

// Mock WebSocket
class MockWebSocket {
    onopen: any;
    onmessage: any;
    onclose: any;
    onerror: any;
    close = vi.fn();
    send = vi.fn();

    static lastInstance: MockWebSocket;

    constructor(public url: string) {
        MockWebSocket.lastInstance = this;
        // Trigger onopen in a microtask
        setTimeout(() => this.onopen?.(), 0);
    }
}

describe('useWebSocket', () => {
    let originalWebSocket: any;

    beforeEach(() => {
        originalWebSocket = (window as any).WebSocket;
        (window as any).WebSocket = MockWebSocket as any;

        vi.mocked(useAuth).mockReturnValue({
            token: 'test-token',
            user: { id: 'u1', username: 'test-user', tenant_id: 'tenant-1' },
            isAuthenticated: true,
            login: vi.fn(),
            logout: vi.fn()
        });

        vi.useFakeTimers();
    });

    afterEach(() => {
        (window as any).WebSocket = originalWebSocket;
        vi.useRealTimers();
        vi.clearAllMocks();
    });

    it('initializes connection and updates status', async () => {
        const { result } = renderHook(() => useWebSocket('/ws/test'));

        expect(result.current.status).toBe('connecting');

        await act(async () => {
            vi.advanceTimersByTime(10);
        });

        expect(result.current.status).toBe('open');
    });

    it('handles incoming log messages', async () => {
        const { result } = renderHook(() => useWebSocket('/ws/test'));

        await act(async () => {
            vi.advanceTimersByTime(10);
        });

        const mockLog = { id: '1', message: 'Test message', level: 'INFO', timestamp: new Date().toISOString(), source: 'src' };

        await act(async () => {
            MockWebSocket.lastInstance.onmessage?.({
                data: JSON.stringify({ type: 'log', payload: mockLog })
            });
        });

        expect(result.current.lastLog).toEqual(mockLog);
    });

    it('transitions to closed status', async () => {
        const { result } = renderHook(() => useWebSocket('/ws/test'));

        await act(async () => {
            vi.advanceTimersByTime(10);
        });

        await act(async () => {
            MockWebSocket.lastInstance.onclose?.({ wasClean: true });
        });

        expect(result.current.status).toBe('closed');
    });
});
