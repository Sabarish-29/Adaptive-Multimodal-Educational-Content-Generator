import React from 'react';
import { screen } from '@testing-library/react';
import { renderWithProviders } from './test-utils';
import AuthorPage from '../pages/author';
jest.mock('next/router', () => ({ useRouter: () => ({ replace: jest.fn(), pathname:'/author' }) }));

const seed = (md: string) => {
  localStorage.setItem('draft:md', md);
  localStorage.setItem('auth:user', JSON.stringify({ id:'u1', role:'instructor', name:'Inst', token:'t'}));
  return renderWithProviders(<AuthorPage />);
};

describe('Author frontmatter parsing', () => {
  test('parses title and objectives list', async () => {
    seed(`---\ntitle: Sample Lesson\nobjectives: add, subtract, multiply\n---\n\nContent body`);
    await screen.findByText(/Sample Lesson/);
    expect(screen.getByText(/add, subtract, multiply/)).toBeInTheDocument();
  });
});
