import React from 'react';
import { render, screen } from '@testing-library/react';
import { RouteGuard } from '../components/RouteGuard';
import { AuthProvider } from '../auth/AuthContext';

jest.mock('next/router', () => ({
  useRouter: () => ({ replace: jest.fn() })
}));

describe('RouteGuard', () => {
  test('blocks children when not authenticated', () => {
    render(
      <AuthProvider>
        <RouteGuard>
          <div data-testid="secret">Secret</div>
        </RouteGuard>
      </AuthProvider>
    );
    expect(screen.queryByTestId('secret')).toBeNull();
  });
  test('renders children when authenticated', async () => {
    localStorage.setItem('auth:user', JSON.stringify({ id:'u1', name:'u1', role:'learner', token:'t' }));
    render(
      <AuthProvider>
        <RouteGuard>
          <div data-testid="secret">Secret</div>
        </RouteGuard>
      </AuthProvider>
    );
    expect(await screen.findByTestId('secret')).toBeInTheDocument();
    localStorage.removeItem('auth:user');
  });
  test('restricts role-based access', async () => {
    localStorage.setItem('auth:user', JSON.stringify({ id:'u2', name:'u2', role:'learner', token:'t' }));
    render(
      <AuthProvider>
        <RouteGuard roles={['instructor']}>
          <div data-testid="instructor">Only Instructor</div>
        </RouteGuard>
      </AuthProvider>
    );
    expect(screen.queryByTestId('instructor')).toBeNull();
    localStorage.removeItem('auth:user');
  });
  test('allows instructor role', async () => {
    localStorage.setItem('auth:user', JSON.stringify({ id:'inst', name:'inst', role:'instructor', token:'t' }));
    render(
      <AuthProvider>
        <RouteGuard roles={['instructor']}>
          <div data-testid="instructor">Only Instructor</div>
        </RouteGuard>
      </AuthProvider>
    );
    expect(await screen.findByTestId('instructor')).toBeInTheDocument();
    localStorage.removeItem('auth:user');
  });
});
