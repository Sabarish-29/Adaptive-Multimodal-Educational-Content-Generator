import React from 'react';
import { screen } from '@testing-library/react';
import { renderWithProviders } from './test-utils';
// marked & DOMPurify are exercised indirectly via the page logic

// We import the actual page component.
import AuthorPage from '../pages/author';
// Mock next/router for RouteGuard usage inside page
jest.mock('next/router', () => ({ useRouter: () => ({ replace: jest.fn(), pathname:'/author' }) }));

// Helper to render within providers with an instructor user.
const renderWithAuth = (markdown: string) => {
  // Seed localStorage with draft before render; component loads it on mount.
  localStorage.setItem('draft:md', markdown);
  // Also store user so RouteGuard passes.
  localStorage.setItem('auth:user', JSON.stringify({ id: 'u1', name: 'Inst', role: 'instructor', token: 't' }));
  return renderWithProviders(<AuthorPage />);
};

describe('Author page sanitization', () => {
  test('removes script tag & dangerous attrs from preview', async () => {
  const malicious = `## Title\n\n<img src=x onerror=alert('xss') />\n<script>window.evil=1</script>`;
    renderWithAuth(malicious);
    // Wait a tick for useEffect markdown parse; using findByText on heading
    let heading: HTMLElement | null = null;
    try {
      heading = await screen.findByRole('heading', { name: 'Title' }, { timeout: 1500 });
    } catch (e){
      // eslint-disable-next-line no-console
      console.log('DOM on failure:', document.body.innerHTML.slice(0,4000));
      throw e;
    }
    expect(heading).toBeInTheDocument();
    const preview = heading.closest('div')?.parentElement?.parentElement?.querySelector('div[dangerouslySetInnerHTML]') || document.querySelector('div[dangerouslySetInnerHTML]');
    // Instead, inspect DOMPurify outcome indirectly: ensure script not present
    expect(document.querySelector('script')).toBeNull();
    const img = document.querySelector('img');
    if(img){
      expect(img.getAttribute('onerror')).toBeNull();
    }
    // Rather than scanning entire body (which includes raw textarea source), focus on preview container only
    const previewHtml = document.querySelector('section[aria-label="Preview"]')?.innerHTML || '';
    expect(previewHtml).not.toContain('window.evil');
  });
});
