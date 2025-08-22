import React from 'react';
import { renderWithProviders, screen, fireEvent } from './test-utils';
import Home from '../pages/index';

describe('Theme toggle', () => {
  it('toggles between dark and light', () => {
  renderWithProviders(<Home />);
    const btn = screen.getByRole('button', { name: /light|dark/i });
    const firstLabel = btn.textContent;
    fireEvent.click(btn);
    expect(btn.textContent).not.toBe(firstLabel);
  });
});
