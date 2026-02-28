import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import AIInsights from '../../components/AIInsights';

describe('AIInsights', () => {
    it('renders nothing when analysis is null', () => {
        const { container } = render(<AIInsights analysis={null} />);
        expect(container.innerHTML).toBe('');
    });

    it('renders the header text', () => {
        const analysis = {
            summary: 'Great product overall.',
            pros: ['Good battery', 'Nice display'],
            cons: ['Expensive'],
            recommendation: 'Buy it!',
        };
        render(<AIInsights analysis={analysis} />);
        expect(screen.getByText('AI Assistant Report')).toBeInTheDocument();
    });

    it('renders all four sections', () => {
        const analysis = {
            summary: 'Overall great.',
            pros: ['Pro 1'],
            cons: ['Con 1'],
            recommendation: 'Yes definitely',
        };
        render(<AIInsights analysis={analysis} />);
        expect(screen.getByText('Executive Summary')).toBeInTheDocument();
        expect(screen.getByText('Key Strengths')).toBeInTheDocument();
        expect(screen.getByText('Critical Issues')).toBeInTheDocument();
        expect(screen.getByText('Buying Recommendation')).toBeInTheDocument();
    });

    it('renders list items for pros', () => {
        const analysis = {
            summary: 'Summary text',
            pros: ['Battery is excellent', 'Display is great'],
            cons: [],
            recommendation: 'Buy it',
        };
        render(<AIInsights analysis={analysis} />);
        expect(screen.getByText('Battery is excellent')).toBeInTheDocument();
        expect(screen.getByText('Display is great')).toBeInTheDocument();
    });
});
