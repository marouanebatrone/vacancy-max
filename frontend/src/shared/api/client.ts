/**
 * The one place that talks HTTP.
 *
 * Every response shape comes from `schema.d.ts`, which is GENERATED from the
 * backend's OpenAPI document (`npm run api:types`). Never hand-write an API
 * type: if the backend changes, the build should break, not production.
 */

/**
 * Same-origin in development (Vite proxies /api to Django), and an absolute URL
 * in production, where the static site and the API are separate Render
 * services. VITE_API_URL is baked in at build time.
 */
const BASE_URL = `${import.meta.env.VITE_API_URL ?? ''}/api/v1`;

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details: unknown = {},
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init.headers },
  });

  const body: unknown = response.status === 204 ? null : await response.json();

  if (!response.ok) {
    const envelope = body as { error?: { code?: string; message?: string; details?: unknown } };
    throw new ApiError(
      response.status,
      envelope.error?.code ?? 'error',
      envelope.error?.message ?? 'Request failed',
      envelope.error?.details,
    );
  }

  return body as T;
}
