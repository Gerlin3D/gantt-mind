import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { type ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { buildNineTaskPlan, demoPlanFixture } from '../../../test/planFixtures';
import { PlanPage } from './PlanPage';

function renderWithQueryClient(children: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(<QueryClientProvider client={queryClient}>{children}</QueryClientProvider>);
}

function mockPlanResponse(plan = demoPlanFixture) {
  const fetchMock = vi.fn((): ReturnType<typeof fetch> => Promise.resolve(Response.json(plan)));
  vi.stubGlobal('fetch', fetchMock);

  return fetchMock;
}

describe('PlanPage', () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows a structured loading state', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        () => new Promise<Response>(() => undefined),
      ),
    );

    renderWithQueryClient(<PlanPage />);

    expect(screen.getByLabelText('Loading Gantt workspace')).toBeInTheDocument();
  });

  it('renders successful plan data, task table rows, Gantt bars, and dependency lines', async () => {
    mockPlanResponse(buildNineTaskPlan());

    const { container } = renderWithQueryClient(<PlanPage />);

    expect(await screen.findByRole('heading', { name: 'GanttMind Demo Project' })).toBeInTheDocument();
    expect(screen.getAllByLabelText(/^Open details for Task /)).toHaveLength(18);
    expect(screen.getByTestId('gantt-bar-task-1')).toHaveStyle({ left: '89px', width: '32px' });
    expect(container.querySelectorAll('.dependency-line')).toHaveLength(9);
  });

  it('labels dependency lines and highlights related dependencies on task hover', async () => {
    mockPlanResponse(demoPlanFixture);
    const { container } = renderWithQueryClient(<PlanPage />);

    expect(await screen.findByLabelText('Project discovery → Requirements baseline')).toBeInTheDocument();

    fireEvent.mouseEnter(screen.getAllByLabelText('Open details for Requirements baseline')[0]);

    expect(container.querySelectorAll('.dependency-line.is-highlighted')).toHaveLength(2);
  });

  it('keeps horizontal pane scroll independent while syncing vertical rows', async () => {
    vi.stubGlobal(
      'requestAnimationFrame',
      vi.fn((callback: FrameRequestCallback) => {
        callback(0);
        return 1;
      }),
    );
    mockPlanResponse(buildNineTaskPlan());

    const { container } = renderWithQueryClient(<PlanPage />);

    expect(await screen.findByRole('heading', { name: 'GanttMind Demo Project' })).toBeInTheDocument();

    const taskPane = container.querySelector('.task-table-pane') as HTMLDivElement;
    const timelinePane = container.querySelector('.timeline-pane') as HTMLDivElement;

    taskPane.scrollLeft = 96;
    taskPane.scrollTop = 88;
    fireEvent.scroll(taskPane);

    expect(timelinePane.scrollTop).toBe(88);
    expect(timelinePane.scrollLeft).toBe(0);

    timelinePane.scrollLeft = 210;
    timelinePane.scrollTop = 132;
    fireEvent.scroll(timelinePane);

    expect(taskPane.scrollTop).toBe(132);
    expect(taskPane.scrollLeft).toBe(96);
  });

  it('opens and closes read-only task details with predecessor and successor names', async () => {
    mockPlanResponse(demoPlanFixture);
    renderWithQueryClient(<PlanPage />);

    const taskOpeners = await screen.findAllByLabelText('Open details for Requirements baseline');

    fireEvent.click(taskOpeners[0]);

    const dialog = screen.getByRole('dialog', { name: 'Requirements baseline' });

    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByText('Project discovery')).toBeInTheDocument();
    expect(within(dialog).getByText('Interactive prototype')).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Escape' });

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  it('shows an error state and retries the request', async () => {
    const fetchMock = vi
      .fn<() => ReturnType<typeof fetch>>()
      .mockResolvedValueOnce(Response.json({ detail: 'seed missing' }, { status: 404 }))
      .mockResolvedValueOnce(Response.json(demoPlanFixture));
    vi.stubGlobal('fetch', fetchMock);

    renderWithQueryClient(<PlanPage />);

    expect(await screen.findByRole('heading', { name: 'Could not load the plan' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));

    expect(await screen.findByRole('heading', { name: 'GanttMind Demo Project' })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('imports a workbook and renders the created plan', async () => {
    const importedPlan = {
      ...demoPlanFixture,
      id: 'imported-plan',
      name: 'Imported Plan',
    };
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit): ReturnType<typeof fetch> => {
      if (String(input).endsWith('/api/plans/import') && init?.method === 'POST') {
        return Promise.resolve(Response.json(importedPlan, { status: 201 }));
      }
      return Promise.resolve(Response.json(demoPlanFixture));
    });
    vi.stubGlobal('fetch', fetchMock);

    renderWithQueryClient(<PlanPage />);

    expect(await screen.findByRole('heading', { name: 'GanttMind Demo Project' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Import Excel' }));
    fireEvent.change(screen.getByLabelText('Workbook'), {
      target: {
        files: [
          new File(['xlsx'], 'plan.xlsx', {
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          }),
        ],
      },
    });
    fireEvent.change(screen.getByLabelText('Plan name'), { target: { value: 'Imported Plan' } });
    fireEvent.change(screen.getByLabelText('Start date'), { target: { value: '2026-01-05' } });
    fireEvent.click(screen.getByRole('button', { name: 'Import' }));

    expect(await screen.findByRole('heading', { name: 'Imported Plan' })).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: 'Import Excel' })).not.toBeInTheDocument();

    const [, importInit] = fetchMock.mock.calls.find(([input]) =>
      String(input).endsWith('/api/plans/import'),
    ) ?? [];
    expect(importInit?.body).toBeInstanceOf(FormData);
  });

  it('shows import row validation errors', async () => {
    const validationPayload = {
      code: 'excel_validation_failed',
      message: 'The workbook contains invalid rows.',
      errors: [
        {
          worksheet: 'Tasks',
          row: 2,
          column: 'duration',
          code: 'invalid_duration',
          message: 'Duration must be a positive integer.',
        },
      ],
    };
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit): ReturnType<typeof fetch> => {
      if (String(input).endsWith('/api/plans/import') && init?.method === 'POST') {
        return Promise.resolve(Response.json(validationPayload, { status: 400 }));
      }
      return Promise.resolve(Response.json(demoPlanFixture));
    });
    vi.stubGlobal('fetch', fetchMock);

    renderWithQueryClient(<PlanPage />);

    expect(await screen.findByRole('heading', { name: 'GanttMind Demo Project' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Import Excel' }));
    fireEvent.change(screen.getByLabelText('Workbook'), {
      target: { files: [new File(['xlsx'], 'plan.xlsx')] },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Import' }));

    expect(await screen.findByText('The workbook contains invalid rows.')).toBeInTheDocument();
    expect(screen.getByText(/invalid_duration/)).toBeInTheDocument();
    expect(screen.getByText(/row 2, duration/)).toBeInTheDocument();
  });

  it('exports the current plan as a downloaded blob', async () => {
    const createObjectUrl = vi.fn(() => 'blob:plan');
    const revokeObjectUrl = vi.fn();
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: createObjectUrl,
      revokeObjectURL: revokeObjectUrl,
    });
    const fetchMock = vi.fn((input: RequestInfo | URL): ReturnType<typeof fetch> => {
      if (String(input).endsWith('/api/plans/demo-plan/export')) {
        return Promise.resolve(
          new Response(new Blob(['xlsx']), {
            headers: {
              'content-disposition': 'attachment; filename="demo.xlsx"',
            },
          }),
        );
      }
      return Promise.resolve(Response.json(demoPlanFixture));
    });
    vi.stubGlobal('fetch', fetchMock);

    renderWithQueryClient(<PlanPage />);

    expect(await screen.findByRole('heading', { name: 'GanttMind Demo Project' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Export Excel' }));

    await waitFor(() => {
      expect(createObjectUrl).toHaveBeenCalledTimes(1);
    });
    expect(revokeObjectUrl).toHaveBeenCalledWith('blob:plan');
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/plans/demo-plan/export', {
      headers: {
        Accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      },
    });
  });

  it('shows an empty state for a plan without tasks', async () => {
    mockPlanResponse({ ...demoPlanFixture, tasks: [], dependencies: [] });

    renderWithQueryClient(<PlanPage />);

    expect(await screen.findByRole('heading', { name: 'No tasks yet' })).toBeInTheDocument();
  });
});
