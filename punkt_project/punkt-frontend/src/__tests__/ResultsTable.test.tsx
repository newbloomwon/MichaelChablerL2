import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ResultsTable } from '../components/search/ResultsTable';
import { LogEntry } from '../components/feed/LiveFeed';

const mockResults: LogEntry[] = [
    {
        id: '1',
        timestamp: new Date().toISOString(),
        level: 'INFO',
        source: 'nginx',
        message: 'Normal operation',
        metadata: { req_id: 'abc' }
    },
    {
        id: '2',
        timestamp: new Date().toISOString(),
        level: 'ERROR',
        source: 'auth-svc',
        message: 'Auth failure',
        metadata: { user: 'mike' }
    }
];

describe('ResultsTable', () => {
    it('renders column headers', () => {
        render(<ResultsTable results={[]} />);
        expect(screen.getByText('Time')).toBeInTheDocument();
        expect(screen.getByText('Level')).toBeInTheDocument();
        expect(screen.getByText('Source')).toBeInTheDocument();
        expect(screen.getByText('Message')).toBeInTheDocument();
    });

    it('renders result items', () => {
        render(<ResultsTable results={mockResults} />);
        expect(screen.getByText('Normal operation')).toBeInTheDocument();
        expect(screen.getByText('Auth failure')).toBeInTheDocument();
        expect(screen.getByText('nginx')).toBeInTheDocument();
        expect(screen.getByText('auth-svc')).toBeInTheDocument();
    });

    it('expands row when chevron is clicked', () => {
        render(<ResultsTable results={mockResults} />);
        const expandButtons = screen.getAllByRole('button');
        fireEvent.click(expandButtons[0]);

        expect(screen.getByText('Full Message')).toBeInTheDocument();
        expect(screen.getByText('Metadata')).toBeInTheDocument();
        expect(screen.getByText('req_id')).toBeInTheDocument();
    });

    it('displays total count in footer', () => {
        render(<ResultsTable results={mockResults} totalCount={100} />);
        expect(screen.getByText(/showing 2 results/i)).toBeInTheDocument();
        expect(screen.getByText(/total: 100/i)).toBeInTheDocument();
    });
});
