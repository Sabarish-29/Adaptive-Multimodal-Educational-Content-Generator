import React from 'react';
import { render } from '@testing-library/react';
import { AuthProvider } from '../auth/AuthContext';
import { AppProviders } from '../components/AppProviders';

import type { RenderResult } from '@testing-library/react';

export function renderWithProviders(ui: React.ReactElement, { auth = true } = {}): RenderResult {
  // Allow disabling auth wrapper if a test purposefully asserts missing provider error
  const tree = auth ? (
    <AuthProvider>
      <AppProviders>{ui}</AppProviders>
    </AuthProvider>
  ) : ui;
  return render(tree);
}

export * from '@testing-library/react';
