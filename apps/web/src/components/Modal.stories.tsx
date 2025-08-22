import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { Modal } from './Modal';
import { Button } from './Button';

const Demo: React.FC<any> = (args) => {
  const [open, setOpen] = useState(true);
  return (
    <div>
      <Button onClick={() => setOpen(true)}>Open Modal</Button>
      <Modal {...args} open={open} onClose={() => setOpen(false)} title="Example Modal" descriptionId="modal-desc">
        <p id="modal-desc">This is example modal content.</p>
      </Modal>
    </div>
  );
};

const meta: Meta<typeof Modal> = {
  title: 'Primitives/Modal',
  component: Modal,
  render: (args) => <Demo {...args} />
};
export default meta;

type Story = StoryObj<typeof Modal>;

export const Basic: Story = { args: { open: false } };
