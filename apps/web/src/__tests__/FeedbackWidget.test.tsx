import React from 'react';
import { renderWithProviders, screen, fireEvent, act } from './test-utils';
import { FeedbackWidget } from '../components/FeedbackWidget';

// Mock services analytics base
jest.mock('../lib/api', () => ({ services: { analytics: 'http://analytics.test' } }));

// Capture telemetry events emitted
const emitted: any[] = [];
jest.mock('../lib/telemetry', () => ({
  emitTelemetry: (e: any) => { emitted.push(e); },
  onTelemetry: () => () => {},
}));

describe('FeedbackWidget', () => {
  beforeEach(()=>{ emitted.length = 0; (global as any).fetch = jest.fn(()=> Promise.resolve({ ok: true, json:()=>Promise.resolve({}) })); });

  it('opens modal and submits positive feedback with tags', async () => {
    renderWithProviders(<FeedbackWidget itemId="bundle123" learnerId="learner_demo" />);
    // View event
    expect(emitted.find(e=>e.type==='feedback.view')).toBeTruthy();
    const upBtn = screen.getByRole('button', { name: /thumbs up/i });
    fireEvent.click(upBtn);
    await screen.findByRole('dialog');
    // select tag
    const tagBtn = screen.getByRole('button', { name: /helpful/i });
    fireEvent.click(tagBtn);
    const submit = screen.getByRole('button', { name: /submit/i });
    await act(async ()=> { fireEvent.click(submit); });
    expect(emitted.find(e=>e.type==='feedback.submit')).toBeTruthy();
    expect(screen.getByText(/Thanks! Saved./i)).toBeInTheDocument();
  });

  it('prevents submit without rating', () => {
    renderWithProviders(<FeedbackWidget itemId="bundle456" />);
    const submitBtn = screen.queryByRole('button', { name: /submit/i });
    // Not opened yet
    expect(submitBtn).toBeNull();
  });
});
