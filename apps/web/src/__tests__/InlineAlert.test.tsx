import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { InlineAlert } from '../components/InlineAlert';

describe('InlineAlert', () => {
  it('renders title and content', () => {
    render(<InlineAlert title="Title">Content</InlineAlert>);
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('calls onClose', () => {
    const fn = jest.fn();
    render(<InlineAlert title="X" onClose={fn}>Close me</InlineAlert>);
    fireEvent.click(screen.getByRole('button', { name: /dismiss/i }));
    expect(fn).toHaveBeenCalled();
  });
});
