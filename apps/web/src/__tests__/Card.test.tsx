import React from 'react';
import { render, screen } from '@testing-library/react';
import { Card } from '../components/Card';

describe('Card', () => {
  it('renders title and children', () => {
    render(<Card title="Hello"><span>Inner</span></Card>);
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Inner')).toBeInTheDocument();
  });
  it('renders footer', () => {
    render(<Card title="T" footer="Foot">X</Card>);
    expect(screen.getByText('Foot')).toBeInTheDocument();
  });
});
