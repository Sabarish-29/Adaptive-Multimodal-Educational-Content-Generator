import type { Meta, StoryObj } from '@storybook/react';
import { InlineAlert } from './InlineAlert';

const meta: Meta<typeof InlineAlert> = {
  title: 'Primitives/InlineAlert',
  component: InlineAlert,
  args: { children: 'Alert content', title: 'Notice' }
};
export default meta;

type Story = StoryObj<typeof InlineAlert>;

export const Info: Story = {};
export const Success: Story = { args: { tone: 'success' } };
export const Warn: Story = { args: { tone: 'warn' } };
export const Error: Story = { args: { tone: 'error', title: 'Error' } };
