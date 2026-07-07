import type { PlanDto } from '../model/types';

const defaultApiBaseUrl = 'http://localhost:8000';

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL ?? defaultApiBaseUrl).replace(/\/+$/, '');
}

function buildApiUrl(path: string) {
  return `${getApiBaseUrl()}${path.startsWith('/') ? path : `/${path}`}`;
}

async function requestPlan(path: string): Promise<PlanDto> {
  const response = await fetch(buildApiUrl(path), {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const payload: unknown = await response.json();

      if (
        typeof payload === 'object' &&
        payload !== null &&
        'detail' in payload &&
        typeof payload.detail === 'string'
      ) {
        message = payload.detail;
      }
    } catch {
      // Keep the status-based message when the API does not return JSON.
    }

    throw new ApiRequestError(message, response.status);
  }

  return response.json() as Promise<PlanDto>;
}

export function getDemoPlan() {
  return requestPlan('/api/plans/demo');
}

export function getPlanById(planId: string) {
  return requestPlan(`/api/plans/${encodeURIComponent(planId)}`);
}
