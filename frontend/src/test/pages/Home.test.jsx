import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Home from '../../pages/Home';

// Mock the api module
vi.mock('../../services/api', () => ({
    startScraping: vi.fn(),
    getScrapeStatus: vi.fn(),
}));

describe('Home', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the heading', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        expect(screen.getByText(/Decode Customer/i)).toBeInTheDocument();
    });

    it('renders the URL input field', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        const input = screen.getByPlaceholderText(/flipkart/i);
        expect(input).toBeInTheDocument();
    });

    it('shows an error when submitting empty URL', async () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        const submitButton = screen.getByRole('button', { name: /analyze/i });
        fireEvent.click(submitButton);
        expect(await screen.findByText(/please enter/i)).toBeInTheDocument();
    });

    it('renders all 4 feature cards', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        expect(screen.getByText('AI Sentiment Analysis')).toBeInTheDocument();
        expect(screen.getByText('Aspect-Based Insights')).toBeInTheDocument();
        expect(screen.getByText('Fake Review Detection')).toBeInTheDocument();
        expect(screen.getByText('Topic Discovery')).toBeInTheDocument();
    });
});
