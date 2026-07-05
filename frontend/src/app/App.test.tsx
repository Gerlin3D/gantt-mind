import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { App } from './App';

describe('App', () => {
  it('renders the stage 1 project shell', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'GanttMind' })).toBeInTheDocument();
    expect(screen.getByText('FastAPI health endpoint')).toBeInTheDocument();
  });
});
