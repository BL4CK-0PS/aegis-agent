/**
 * AEGIS API Client
 * Base HTTP wrapper providing typed responses, timeout enforcement,
 * and robust failure handling.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiError extends Error {
  public status?: number;
  public details?: any;

  constructor(message: string, status?: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export async function apiClient<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeoutMs = 12000, ...fetchOptions } = options;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  const url = cleanPath.startsWith('/api') ? cleanPath : `${API_BASE}${cleanPath}`;

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(fetchOptions.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorBody: any = null;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }

      const detail =
        typeof errorBody === 'object' && errorBody !== null
          ? errorBody.detail || errorBody.message || JSON.stringify(errorBody)
          : String(errorBody);

      throw new ApiError(
        `Backend API error (${response.status}): ${detail || response.statusText}`,
        response.status,
        errorBody
      );
    }

    return (await response.json()) as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new ApiError(`Request timeout after ${timeoutMs}ms calling ${url}`);
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      `Network error or backend unavailable at ${url}. Ensure FastAPI is running on port 8000. Detail: ${err.message}`
    );
  }
}

export async function checkBackendHealth(): Promise<{ status: string; service: string }> {
  return apiClient<{ status: string; service: string }>('/health', { timeoutMs: 3000 });
}
