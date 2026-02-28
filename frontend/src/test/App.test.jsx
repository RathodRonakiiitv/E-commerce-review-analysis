import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

describe('App', () => {
    it('renders without crashing', () => {
        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );
        // App should render the layout with navigation
        expect(document.body).toBeTruthy();
    });

    it('renders the home page by default', () => {
        render(
            <MemoryRouter initialEntries={['/']}>
                <App />
            </MemoryRouter>
        );
        // Home page should show the search input or heading
        expect(screen.getByText(/Decode Customer/i)).toBeInTheDocument();
    });
});
