import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppQueryProvider } from './providers/QueryProvider';
import { demoPlanFixture } from '../test/planFixtures';
import { App } from './App';

describe('App', () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the demo plan shell', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((): ReturnType<typeof fetch> =>
        Promise.resolve(Response.json(demoPlanFixture)),
      ),
    );

    render(
      <AppQueryProvider>
        <App />
      </AppQueryProvider>,
    );

    expect(await screen.findByRole('heading', { name: 'GanttMind Demo Project' })).toBeInTheDocument();
    expect(screen.getByLabelText('Gantt workspace')).toBeInTheDocument();
  });
});
