import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

// Mock axios
vi.mock('axios', () => {
    const instance = {
        get: vi.fn(),
        post: vi.fn(),
        delete: vi.fn(),
    };
    return {
        default: {
            create: vi.fn(() => instance),
        },
    };
});

// Must import AFTER mocking axios
let api;
beforeEach(async () => {
    vi.resetModules();
    api = await import('../../services/api');
});

describe('API service', () => {
    it('exports getProducts function', () => {
        expect(typeof api.getProducts).toBe('function');
    });

    it('exports getProductAnalysis function', () => {
        expect(typeof api.getProductAnalysis).toBe('function');
    });

    it('exports startScraping function', () => {
        expect(typeof api.startScraping).toBe('function');
    });

    it('exports exportPDF function', () => {
        expect(typeof api.exportPDF).toBe('function');
    });

    it('exports getAISummary function', () => {
        expect(typeof api.getAISummary).toBe('function');
    });

    it('exports getHealth function', () => {
        expect(typeof api.getHealth).toBe('function');
    });
});
