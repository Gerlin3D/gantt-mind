import type {
  ExportPlanResult,
  ImportPlanRequest,
  ImportValidationErrorPayload,
  PlanDto,
} from '../model/types';

const defaultApiBaseUrl = 'http://localhost:8000';

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly payload?: unknown,
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

async function readError(response: Response): Promise<{ message: string; payload?: unknown }> {
  const message = `Request failed with status ${response.status}`;

  try {
    const payload: unknown = await response.json();

    if (
      typeof payload === 'object' &&
      payload !== null &&
      'message' in payload &&
      typeof payload.message === 'string'
    ) {
      return { message: payload.message, payload };
    }
    if (
      typeof payload === 'object' &&
      payload !== null &&
      'detail' in payload &&
      typeof payload.detail === 'string'
    ) {
      return { message: payload.detail, payload };
    }
    return { message, payload };
  } catch {
    return { message };
  }
}

function filenameFromContentDisposition(header: string | null, fallback: string) {
  if (!header) {
    return fallback;
  }

  const match = /filename="?([^";]+)"?/i.exec(header);
  return match?.[1] ?? fallback;
}

export function getDemoPlan() {
  return requestPlan('/api/plans/demo');
}

export function getPlanById(planId: string) {
  return requestPlan(`/api/plans/${encodeURIComponent(planId)}`);
}

export function getSampleWorkbookUrl() {
  return buildApiUrl('/api/plans/import/sample');
}

export async function importPlan(request: ImportPlanRequest) {
  const formData = new FormData();
  formData.append('file', request.file);
  formData.append('plan_name', request.planName);
  formData.append('start_date', request.startDate);

  const response = await fetch(buildApiUrl('/api/plans/import'), {
    method: 'POST',
    body: formData,
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    const { message, payload } = await readError(response);
    throw new ApiRequestError(message, response.status, payload);
  }

  return response.json() as Promise<PlanDto>;
}

export async function exportPlan(planId: string): Promise<ExportPlanResult> {
  const response = await fetch(buildApiUrl(`/api/plans/${encodeURIComponent(planId)}/export`), {
    headers: {
      Accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    },
  });

  if (!response.ok) {
    const { message, payload } = await readError(response);
    throw new ApiRequestError(message, response.status, payload);
  }

  return {
    blob: await response.blob(),
    filename: filenameFromContentDisposition(response.headers.get('content-disposition'), `${planId}.xlsx`),
  };
}

export function isImportValidationErrorPayload(
  payload: unknown,
): payload is ImportValidationErrorPayload {
  return (
    typeof payload === 'object' &&
    payload !== null &&
    'code' in payload &&
    payload.code === 'excel_validation_failed' &&
    'errors' in payload &&
    Array.isArray(payload.errors)
  );
}
