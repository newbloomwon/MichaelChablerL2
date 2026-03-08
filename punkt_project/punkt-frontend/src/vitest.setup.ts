import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock ResizeObserver for Recharts and TanStack Virtual
class ResizeObserver {
    observe() { }
    unobserve() { }
    disconnect() { }
}

window.ResizeObserver = ResizeObserver;

// Mock layout methods for TanStack Virtual in JSDOM
Element.prototype.getBoundingClientRect = function () {
    const el = this as unknown as HTMLElement;
    return {
        width: parseFloat(el.style?.width) || 1000,
        height: parseFloat(el.style?.height) || 800,
        top: 0,
        left: 0,
        bottom: 0,
        right: 0,
        x: 0,
        y: 0,
        toJSON: () => { }
    } as DOMRect;
};

Object.defineProperty(HTMLElement.prototype, 'offsetHeight', { configurable: true, value: 800 });
Object.defineProperty(HTMLElement.prototype, 'offsetWidth', { configurable: true, value: 1000 });

// Mock URL.createObjectURL for CSV downloads
window.URL.createObjectURL = vi.fn(() => 'mock-url');
window.URL.revokeObjectURL = vi.fn();
