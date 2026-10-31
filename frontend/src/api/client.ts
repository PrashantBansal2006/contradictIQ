/**
 * ContradictIQ Typed API Client (Phase 0 - Task 0.3)
 * Uses VITE_API_URL and standard ErrorBody envelope
 */

import { ErrorResponse, ErrorDetail } from '../types';

export class ApiError extends Error {
  public code: string;
  public details?: Record<string, unknown> | null;
  public status: number;

  constructor(status: number, errorDetail: ErrorDetail) {
    super(errorDetail.message || `API Error: ${errorDetail.code}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = errorDetail.code;
    this.details = errorDetail.details;
  }
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/+$/, '');
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  private getToken(): string | null {
    try {
      return localStorage.getItem('contradictiq_token');
    } catch {
      return null;
    }
  }

  public setToken(token: string | null): void {
    try {
      if (token) {
        localStorage.setItem('contradictiq_token', token);
      } else {
        localStorage.removeItem('contradictiq_token');
      }
    } catch {
      // Ignore in restricted environments
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const token = this.getToken();

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle non-2xx responses
      if (!response.ok) {
        let errorDetail: ErrorDetail = {
          code: `HTTP_${response.status}`,
          message: response.statusText || 'Unknown Server Error',
        };

        try {
          const body = (await response.json()) as ErrorResponse;
          if (body && body.error) {
            errorDetail = body.error;
          }
        } catch {
          // If response body is not JSON, retain default errorDetail
        }

        throw new ApiError(response.status, errorDetail);
      }

      if (response.status === 204) {
        return {} as T;
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        throw err;
      }

      const errorDetail: ErrorDetail = {
        code: 'NETWORK_ERROR',
        message: err instanceof Error ? err.message : 'Network request failed',
      };
      throw new ApiError(0, errorDetail);
    }
  }

  public get<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
    let query = '';
    if (params) {
      const filtered = Object.entries(params)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join('&');
      if (filtered) {
        query = `?${filtered}`;
      }
    }
    return this.request<T>(`${endpoint}${query}`, { method: 'GET' });
  }

  public post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data instanceof FormData ? data : JSON.stringify(data),
    });
  }

  public patch<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  public delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  /**
   * Health ping to verify backend connectivity (returns status object)
   */
  public async checkHealth(): Promise<{ ok: boolean; message?: string }> {
    try {
      // Backend may mount health at /health or /api/health
      const rootUrl = this.baseUrl.replace(/\/api$/, '');
      const res = await fetch(`${rootUrl}/api/health`).catch(() => fetch(`${rootUrl}/health`));
      if (res && res.ok) {
        const data = await res.json().catch(() => ({ status: 'ok' }));
        return { ok: true, message: data.status || 'ok' };
      }
      return { ok: false, message: `Status ${res.status}` };
    } catch {
      return { ok: false, message: 'Unreachable' };
    }
  }
}

export const api = new ApiClient();
export default api;
