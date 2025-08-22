import type { Meta, StoryObj } from '@storybook/react';
import { Tooltip } from './Tooltip';
import { Button } from './Button';

const meta: Meta<typeof Tooltip> = {
  title: 'Primitives/Tooltip',
  component: Tooltip,
  args: { label: 'Tooltip text', children: <Button>Hover me</Button> }
};
export default meta;

type Story = StoryObj<typeof Tooltip>;

export const Basic: Story = {};
export const Slow: Story = { args: { delay: 800 } };
