import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { useToast } from './Toast';
import { Button } from './Button';

const meta: Meta = {
  title: 'Primitives/Toast',
  parameters: { controls: { disable: true } }
};
export default meta;

type Story = StoryObj;

const Demo: React.FC = () => {
  const { push } = useToast();
  return (
    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
      <Button onClick={()=> push({ message: 'Info toast' })}>Info</Button>
      <Button onClick={()=> push({ message: 'Success!', type: 'success', focus: true })}>Success (focus)</Button>
      <Button onClick={()=> push({ message: 'Warning issued', type: 'warn' })}>Warn</Button>
      <Button onClick={()=> push({ message: 'Something broke', type: 'error' })}>Error</Button>
      <Button onClick={()=> { for(let i=0;i<7;i++){ push({ message: 'Toast #' + (i+1) }); } }}>Overflow (limit)</Button>
      <Button onClick={()=> push({ message: 'Persistent (no auto dismiss)', ttl: 0 })}>Persistent</Button>
    </div>
  );
};

export const Playground: Story = {
  render: () => <Demo />
};
