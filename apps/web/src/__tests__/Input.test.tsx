import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '../components/Input';

describe('Input', () => {
  it('renders label and updates value', () => {
    const { container } = render(<Input label="Name" />);
    const input = container.querySelector('input') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'abc' } });
    expect(input.value).toBe('abc');
    expect(screen.getByText('Name')).toBeInTheDocument();
  });
  it('shows error over helperText', () => {
    const { container } = render(<Input label="X" helperText="help" error="err" />);
    expect(screen.getByText('err')).toBeInTheDocument();
    expect(container.textContent).not.toContain('help');
  });
});
