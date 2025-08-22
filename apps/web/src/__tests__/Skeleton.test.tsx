import React from 'react';
import { render } from '@testing-library/react';
import { Skeleton } from '../components/Skeleton';

describe('Skeleton', () => {
  it('renders with custom dimensions', () => {
    const { container } = render(<Skeleton width={120} height={10} />);
    const span = container.querySelector('span');
    expect(span).toBeInTheDocument();
    expect(span?.getAttribute('style')).toContain('height: 10px');
  });
});
