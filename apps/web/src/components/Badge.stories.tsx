import type { Meta, StoryObj } from '@storybook/react';
import { Badge } from './Badge';

const meta: Meta<typeof Badge> = {
  title: 'Primitives/Badge',
  component: Badge,
  args: { children: 'Badge' }
};
export default meta;

type Story = StoryObj<typeof Badge>;

export const Default: Story = {};
export const Outline: Story = { args: { variant: 'outline' } };
export const Success: Story = { args: { color: 'success' } };
export const Error: Story = { args: { color: 'error' } };
