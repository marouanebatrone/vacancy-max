import { afterEach, describe, expect, it, vi } from 'vitest';

import { ApiError, request } from '@/shared/api/client';

function mockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('request', () => {
  it('returns the parsed body on success', async () => {
    vi.stubGlobal('fetch', mockFetch(200, { years: [2026, 2027] }));

    await expect(request('/calendars/years/')).resolves.toEqual({ years: [2026, 2027] });
  });

  it('prefixes the API base path', async () => {
    const fetchMock = mockFetch(200, {});
    vi.stubGlobal('fetch', fetchMock);

    await request('/calendars/years/');

    expect(fetchMock).toHaveBeenCalledWith('/api/v1/calendars/years/', expect.anything());
  });

  it('unpacks the error envelope into an ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch(404, {
        error: { code: 'unsupported_year', message: 'No holiday data for 2030.', details: {} },
      }),
    );

    await expect(request('/calendars/years/2030/')).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
      code: 'unsupported_year',
      message: 'No holiday data for 2030.',
    });
  });

  it('still raises ApiError when the body is not an envelope', async () => {
    vi.stubGlobal('fetch', mockFetch(500, {}));

    await expect(request('/x')).rejects.toBeInstanceOf(ApiError);
  });
});
