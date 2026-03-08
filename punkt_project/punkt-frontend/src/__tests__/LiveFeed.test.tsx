import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LiveFeed, LogEntry } from '../components/feed/LiveFeed';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../context/AuthContext';

// Mock the hooks
vi.mock('../hooks/useWebSocket');
vi.mock('../context/AuthContext');

const mockLog: LogEntry = {
    id: '1',
    timestamp: new Date().toISOString(),
    level: 'INFO',
    source: 'test-src',
    message: 'Test message'
};

describe('LiveFeed', () => {
    beforeEach(() => {
        vi.mocked(useAuth).mockReturnValue({
            user: { id: 'u1', username: 'test-user', tenant_id: 'test-tenant' },
            isAuthenticated: true,
            login: vi.fn(),
            logout: vi.fn(),
            token: 'test-token'
        });

        vi.mocked(useWebSocket).mockReturnValue({
            status: 'open',
            lastLog: null,
            error: null,
            reconnect: vi.fn(),
        });
    });

    it('renders and shows connection status', () => {
        render(<LiveFeed />);
        expect(screen.getByText(/live log stream/i)).toBeInTheDocument();
        expect(screen.getByText('open')).toBeInTheDocument();
    });

    it('shows waiting message when no logs are present', () => {
        render(<LiveFeed />);
        expect(screen.getByText(/waiting for logs stream/i)).toBeInTheDocument();
    });

    it('displays incoming logs', () => {
        vi.mocked(useWebSocket).mockReturnValue({
            status: 'open',
            lastLog: mockLog,
            error: null,
            reconnect: vi.fn(),
        });

        render(<LiveFeed />);
        expect(screen.getByText('Test message')).toBeInTheDocument();
        expect(screen.getByText(/test-src:/i)).toBeInTheDocument();
    });

    it('pauses and increments unread count', () => {
        const { rerender } = render(<LiveFeed />);

        // Pause
        const pauseBtn = screen.getByText('Pause');
        fireEvent.click(pauseBtn);
        expect(screen.getByText('Resume')).toBeInTheDocument();

        // Simulate incoming log while paused
        vi.mocked(useWebSocket).mockReturnValue({
            status: 'open',
            lastLog: { ...mockLog, id: '2', message: 'Paused message' },
            error: null,
            reconnect: vi.fn(),
        });

        rerender(<LiveFeed />);

        expect(screen.getByText(/1 new logs buffered/i)).toBeInTheDocument();
    });

    it('clears logs when button is clicked', () => {
        vi.mocked(useWebSocket).mockReturnValue({
            status: 'open',
            lastLog: mockLog,
            error: null,
            reconnect: vi.fn(),
        });

        const onClearMock = vi.fn();
        render(<LiveFeed onClear={onClearMock} />);

        const clearBtn = screen.getByTitle('Clear logs');
        fireEvent.click(clearBtn);

        expect(screen.getByText(/waiting for logs stream/i)).toBeInTheDocument();
        expect(onClearMock).toHaveBeenCalled();
    });
});
