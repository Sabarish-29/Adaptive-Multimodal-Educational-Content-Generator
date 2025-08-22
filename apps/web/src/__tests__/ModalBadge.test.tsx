import React from 'react';
import { renderWithProviders, screen, fireEvent } from './test-utils';
import Home from '../pages/index';

// Minimal smoke test for Badge + Modal integration

describe('Modal & Badge primitives', () => {
  it('renders badges and opens modal', () => {
  renderWithProviders(<Home />);
    expect(screen.getByText(/alpha/i)).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: /show modal/i });
    fireEvent.click(btn);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    // Close via button
    const close = screen.getByRole('button', { name: /close/i });
    fireEvent.click(close);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('closes modal on escape and backdrop click', () => {
  renderWithProviders(<Home />);
    fireEvent.click(screen.getByRole('button', { name: /show modal/i }));
    const dialog = screen.getByRole('dialog');
    // Escape
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    // Reopen and click backdrop
    fireEvent.click(screen.getByRole('button', { name: /show modal/i }));
    const dialog2 = screen.getByRole('dialog');
    fireEvent.mouseDown(dialog2.parentElement!); // parent backdrop
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
  
  it('badge variants render', () => {
  renderWithProviders(<Home />);
    expect(screen.getByText(/alpha/i)).toBeInTheDocument();
    expect(screen.getByText(/stable core/i)).toBeInTheDocument();
    expect(screen.getByText(/wip/i)).toBeInTheDocument();
  });
});
