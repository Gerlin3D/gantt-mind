import { beforeEach, describe, expect, it, vi } from 'vitest';
import { demoPlanFixture } from '../../../test/planFixtures';
import { exportPlan, getDemoPlan, getPlanById, getSampleWorkbookUrl, importPlan } from './plansApi';

function mockFetch(response: Response) {
  const fetchMock = vi.fn(
    (input: RequestInfo | URL, init?: RequestInit): ReturnType<typeof fetch> => {
      void input;
      void init;
      return Promise.resolve(response);
    },
  );
  vi.stubGlobal('fetch', fetchMock);

  return fetchMock;
}

describe('plansApi', () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it('requests the demo plan from the configured API path', async () => {
    const fetchMock = mockFetch(Response.json(demoPlanFixture));

    await expect(getDemoPlan()).resolves.toEqual(demoPlanFixture);

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/plans/demo', {
      headers: {
        Accept: 'application/json',
      },
    });
  });

  it('encodes plan IDs', async () => {
    const fetchMock = mockFetch(Response.json(demoPlanFixture));

    await getPlanById('plan with space');

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/plans/plan%20with%20space', {
      headers: {
        Accept: 'application/json',
      },
    });
  });

  it('builds the sample workbook URL', () => {
    expect(getSampleWorkbookUrl()).toBe('http://localhost:8000/api/plans/import/sample');
  });

  it('throws a typed error for non-2xx responses', async () => {
    mockFetch(Response.json({ detail: 'Plan was not found: missing' }, { status: 404 }));

    await expect(getPlanById('missing')).rejects.toMatchObject({
      name: 'ApiRequestError',
      message: 'Plan was not found: missing',
      status: 404,
    });
  });

  it('submits multipart import data', async () => {
    const fetchMock = mockFetch(Response.json(demoPlanFixture));
    const file = new File(['xlsx'], 'plan.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    await expect(
      importPlan({
        file,
        planName: 'Imported',
        startDate: '2026-01-05',
      }),
    ).resolves.toEqual(demoPlanFixture);

    const [, init] = fetchMock.mock.calls[0];
    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:8000/api/plans/import');
    expect(init?.method).toBe('POST');
    expect(init?.headers).toEqual({ Accept: 'application/json' });
    expect(init?.body).toBeInstanceOf(FormData);
  });

  it('throws validation payloads for failed imports', async () => {
    const payload = {
      code: 'excel_validation_failed',
      message: 'The workbook contains invalid rows.',
      errors: [{ row: 2, column: 'duration', code: 'invalid_duration', message: 'Bad' }],
    };
    mockFetch(Response.json(payload, { status: 400 }));

    await expect(
      importPlan({
        file: new File(['xlsx'], 'plan.xlsx'),
        planName: 'Imported',
        startDate: '2026-01-05',
      }),
    ).rejects.toMatchObject({
      name: 'ApiRequestError',
      status: 400,
      payload,
    });
  });

  it('downloads an exported plan blob and filename', async () => {
    const response = new Response(new Blob(['xlsx']), {
      headers: {
        'content-disposition': 'attachment; filename="exported-plan.xlsx"',
      },
    });
    const fetchMock = mockFetch(response);

    await expect(exportPlan('plan 1')).resolves.toMatchObject({
      filename: 'exported-plan.xlsx',
    });

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/plans/plan%201/export', {
      headers: {
        Accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      },
    });
  });
});
