import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SearchBar } from '../components/search/SearchBar';

describe('SearchBar', () => {
    it('renders with placeholder text', () => {
        render(<SearchBar onSearch={() => { }} />);
        expect(screen.getByPlaceholderText(/level=ERROR/i)).toBeInTheDocument();
    });

    it('handles input changes', () => {
        render(<SearchBar onSearch={() => { }} />);
        const input = screen.getByPlaceholderText(/level=ERROR/i) as HTMLInputElement;
        fireEvent.change(input, { target: { value: 'level=WARN' } });
        expect(input.value).toBe('level=WARN');
    });

    it('calls onSearch when Enter key is pressed', () => {
        const onSearchMock = vi.fn();
        render(<SearchBar onSearch={onSearchMock} />);
        const input = screen.getByPlaceholderText(/level=ERROR/i);
        fireEvent.change(input, { target: { value: 'level=INFO' } });
        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
        expect(onSearchMock).toHaveBeenCalledWith('level=INFO', '15m');
    });

    it('calls onSearch when Search button is clicked', () => {
        const onSearchMock = vi.fn();
        render(<SearchBar onSearch={onSearchMock} />);
        const input = screen.getByPlaceholderText(/level=ERROR/i);
        fireEvent.change(input, { target: { value: 'level=DEBUG' } });
        const button = screen.getByRole('button', { name: /^search$/i });
        fireEvent.click(button);
        expect(onSearchMock).toHaveBeenCalledWith('level=DEBUG', '15m');
    });

    it('switches time range presets', () => {
        const onSearchMock = vi.fn();
        render(<SearchBar onSearch={onSearchMock} />);
        const btn24h = screen.getByText('24h');
        fireEvent.click(btn24h);

        const searchBtn = screen.getByRole('button', { name: /^search$/i });
        fireEvent.click(searchBtn);

        expect(onSearchMock).toHaveBeenCalledWith('', '24h');
    });

    it('shows help tooltip when help icon is clicked', () => {
        render(<SearchBar onSearch={() => { }} />);
        const helpBtn = screen.getByTitle('Search help');
        fireEvent.click(helpBtn);
        expect(screen.getByText('Query Language Examples')).toBeInTheDocument();
    });

    it('disables input and button when isLoading is true', () => {
        render(<SearchBar onSearch={() => { }} isLoading={true} />);
        expect(screen.getByPlaceholderText(/level=ERROR/i)).toBeDisabled();
        expect(screen.getByRole('button', { name: '...' })).toBeDisabled();
    });
});
