function handleUnauthorized(): never {
  window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
  throw new Error('Unauthorized — redirecting to login');
}

/**
 * Shared fetcher for SWR hooks.
 * On 401, redirects to /login so stale sessions (e.g. PWA) recover gracefully.
 */
export const authedFetcher = (url: string) =>
  fetch(url).then((res) => {
    if (res.status === 401) handleUnauthorized();
    if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
    return res.json();
  });

/**
 * Check a fetch Response for 401 and redirect if needed.
 * Use in mutation calls: `checkAuth(res)` before processing the response.
 */
export function checkAuth(res: Response): void {
  if (res.status === 401) handleUnauthorized();
}
