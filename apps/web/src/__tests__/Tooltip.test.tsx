import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import { Tooltip } from '../components/Tooltip';
import { Button } from '../components/Button';

jest.useFakeTimers();

describe('Tooltip', () => {
  it('shows after delay on hover', () => {
    render(<Tooltip label="Hello" delay={300}><Button>Trigger</Button></Tooltip>);
    const btn = screen.getByRole('button', { name: /trigger/i });
  act(()=>{ fireEvent.mouseEnter(btn); });
    expect(screen.queryByRole('tooltip')).toBeNull();
    act(()=>{ jest.advanceTimersByTime(310); });
    expect(screen.getByRole('tooltip')).toHaveTextContent('Hello');
  });

  it('hides on mouse leave', () => {
    render(<Tooltip label="Bye" delay={0}><Button>Trigger</Button></Tooltip>);
    const btn = screen.getByRole('button', { name: /trigger/i });
  act(()=>{ fireEvent.mouseEnter(btn); });
    act(()=>{ jest.advanceTimersByTime(1); });
    expect(screen.getByRole('tooltip')).toBeInTheDocument();
  act(()=>{ fireEvent.mouseLeave(btn); });
    expect(screen.queryByRole('tooltip')).toBeNull();
  });
});
