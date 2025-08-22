import React from 'react';
import type { Preview } from '@storybook/react';
import { AppProviders } from '../src/components/AppProviders';

const preview: Preview = {
  decorators: [
    (Story) => (
      <AppProviders>
        <div style={{ padding: 24 }}>
          <Story />
        </div>
      </AppProviders>
    )
  ],
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: { matchers: { color: /(background|color)$/i, date: /Date$/ } }
  }
};

export default preview;
