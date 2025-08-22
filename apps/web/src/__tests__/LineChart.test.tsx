import React from 'react';
import { render, screen } from '@testing-library/react';
import { LineChart } from '../components/charts/LineChart';

describe('LineChart', () => {
  test('renders empty state when no data', () => {
    render(<LineChart data={[]} />);
    expect(screen.getByText(/No data/i)).toBeInTheDocument();
  });
  test('renders svg path with data', () => {
    const data = [ { x:0, y:1 }, { x:1, y:3 }, { x:2, y:2 } ];
    render(<LineChart data={data} />);
    const svg = screen.getByRole('img', { name: /line chart/i });
    expect(svg).toBeInTheDocument();
    const path = svg.querySelector('path');
    expect(path).not.toBeNull();
    expect(path?.getAttribute('d')).toMatch(/^M/);
  });
});
