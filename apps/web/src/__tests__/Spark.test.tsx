import React from 'react';
import { render, screen } from '@testing-library/react';
import { Spark } from '../components/charts/Spark';

describe('Spark', () => {
  test('renders svg with values', () => {
    render(<Spark values={[1,3,2,4]} />);
    const svg = screen.getByRole('img', { name: /spark line/i });
    expect(svg).toBeInTheDocument();
  });
  test('renders placeholder when no values', () => {
    render(<Spark values={[]} />);
    expect(screen.getByText(/No data/i)).toBeInTheDocument();
  });
});
