import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FileUpload } from '../components/upload/FileUpload';
import api from '../lib/api';

vi.mock('../lib/api');

describe('FileUpload', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders and accepts file selection', () => {
        const { container } = render(<FileUpload />);
        const input = container.querySelector('input[type="file"]') as HTMLInputElement;
        const file = new File(['{"level":"info"}'], 'logs.json', { type: 'application/json' });

        fireEvent.change(input, { target: { files: [file] } });

        expect(screen.getByText('logs.json')).toBeInTheDocument();
        // Since the input value is cleared/changed, we check the displayed text
        expect(screen.getByText(/logs\.json/i)).toBeInTheDocument();
    });

    it('handles successful chunked upload flow', async () => {
        const file = new File(['x'.repeat(2 * 1024 * 1024)], 'large.json', { type: 'application/json' }); // 2MB = 2 chunks

        // Mock init
        vi.mocked(api.post).mockResolvedValueOnce({
            data: { success: true, data: { upload_id: 'up-123' } }
        });

        // Mock 2 chunks
        vi.mocked(api.post).mockResolvedValueOnce({ data: { success: true } });
        vi.mocked(api.post).mockResolvedValueOnce({ data: { success: true } });

        // Mock complete
        vi.mocked(api.post).mockResolvedValueOnce({
            data: { success: true, data: { job_id: 'job-456' } }
        });

        const onCompleteMock = vi.fn();
        const { container } = render(<FileUpload onComplete={onCompleteMock} />);

        const input = container.querySelector('input[type="file"]') as HTMLInputElement;
        fireEvent.change(input, { target: { files: [file] } });

        const uploadBtn = screen.getByRole('button', { name: /start ingestion/i });
        fireEvent.click(uploadBtn);

        await waitFor(() => {
            expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
        }, { timeout: 5000 });

        expect(onCompleteMock).toHaveBeenCalledWith('job-456');
    });

    it('shows error if initialization fails', async () => {
        const file = new File(['test'], 'test.json', { type: 'application/json' });
        vi.mocked(api.post).mockResolvedValueOnce({
            data: { success: false, error: { message: 'Server busy' } }
        });

        const { container } = render(<FileUpload />);
        const input = container.querySelector('input[type="file"]') as HTMLInputElement;
        fireEvent.change(input, { target: { files: [file] } });

        const uploadBtn = screen.getByRole('button', { name: /start ingestion/i });
        fireEvent.click(uploadBtn);

        await waitFor(() => {
            expect(screen.getByText('Server busy')).toBeInTheDocument();
        });
    });
});
