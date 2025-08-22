import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import AuthorPage from '../pages/author';
import { AuthProvider } from '../auth/AuthContext';
import { AppProviders } from '../components/AppProviders';
// Mock next/router so RouteGuard doesn't crash in jsdom
jest.mock('next/router', () => ({ useRouter: () => ({ replace: jest.fn(), pathname:'/author' }) }));

const setup = () => {
  // Seed correct key consumed by AuthProvider
  localStorage.setItem('auth:user', JSON.stringify({ id:'u2', name:'Inst2', role:'instructor', token:'t' }));
  localStorage.removeItem('draft:md');
  jest.useFakeTimers();
  render(<AuthProvider><AppProviders><AuthorPage/></AppProviders></AuthProvider>);
};

describe('Author autosave debounce', () => {
  afterEach(()=>{ jest.useRealTimers(); });
  test('saves after 600ms debounce', () => {
    setup();
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: '## New Title' } });
    expect(screen.getByText(/Saving/i)).toBeInTheDocument();
    act(()=>{ jest.advanceTimersByTime(650); });
    const saved = screen.getByText(/Saved/);
    expect(saved).toBeInTheDocument();
    expect(localStorage.getItem('draft:md')).toContain('New Title');
  });
});
