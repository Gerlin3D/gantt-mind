import { beforeEach, describe, expect, it, vi } from 'vitest';
import { demoPlanFixture } from '../../../test/planFixtures';
import { getDemoPlan, getPlanById } from './plansApi';

function mockFetch(response: Response) {
  const fetchMock = vi.fn((): ReturnType<typeof fetch> => Promise.resolve(response));
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

  it('throws a typed error for non-2xx responses', async () => {
    mockFetch(Response.json({ detail: 'Plan was not found: missing' }, { status: 404 }));

    await expect(getPlanById('missing')).rejects.toMatchObject({
      name: 'ApiRequestError',
      message: 'Plan was not found: missing',
      status: 404,
    });
  });
});
