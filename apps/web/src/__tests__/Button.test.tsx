import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../components/Button';

describe('Button', () => {
  it('renders label and handles click', () => {
    const fn = jest.fn();
    render(<Button onClick={fn}>Click Me</Button>);
    fireEvent.click(screen.getByText('Click Me'));
    expect(fn).toHaveBeenCalled();
  });
});
