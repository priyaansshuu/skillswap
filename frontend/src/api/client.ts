const TOKEN_KEY = "skillswap-session";
type StoredSession = { token: string; expiresAt: number };
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: { field: string; message: string }[] = [],
  ) {
    super(message);
  }
}
export function session(): StoredSession | null {
  try {
    const item = JSON.parse(
      sessionStorage.getItem(TOKEN_KEY) || "null",
    ) as StoredSession | null;
    if (item && typeof item.token === "string" && item.expiresAt > Date.now())
      return item;
  } catch {
    /* Corrupt or unavailable storage must not authenticate a member. */
  }
  sessionStorage.removeItem(TOKEN_KEY);
  return null;
}
export function saveSession(token: string, seconds: number) {
  sessionStorage.setItem(
    TOKEN_KEY,
    JSON.stringify({ token, expiresAt: Date.now() + seconds * 1000 }),
  );
}
export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof URLSearchParams))
    headers.set("Content-Type", "application/json");
  const current = session();
  if (current) headers.set("Authorization", "Bearer " + current.token);
  let response: Response;
  try {
    response = await fetch("/api/v1" + path, { ...options, headers });
  } catch {
    throw new ApiError(
      0,
      "NETWORK_ERROR",
      "Cannot reach SkillSwap. Check that the backend is running, then try again.",
    );
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const error = payload.error || {};
    if (response.status === 401 && current) {
      clearSession();
      window.dispatchEvent(new Event("skillswap:expired"));
    }
    throw new ApiError(
      response.status,
      error.code || "REQUEST_FAILED",
      error.message || "This action could not be completed.",
      error.details || [],
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export const post = <T>(path: string, body?: unknown, headers?: HeadersInit) =>
  api<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
    headers,
  });
export const put = <T>(path: string, body: unknown) =>
  api<T>(path, { method: "PUT", body: JSON.stringify(body) });
export const patch = <T>(path: string, body: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
export const remove = (path: string) => api<void>(path, { method: "DELETE" });
export function query(params: Record<string, string | number | undefined>) {
  const result = new URLSearchParams();
  for (const [key, value] of Object.entries(params))
    if (value !== undefined && value !== "") result.set(key, String(value));
  return result.toString();
}
export async function allPages<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T[]> {
  const result: T[] = [];
  for (let offset = 0; ; offset += 100) {
    const page = await api<{ items: T[] }>(
      path + (path.includes("?") ? "&" : "?") + "limit=100&offset=" + offset,
      { signal },
    );
    result.push(...page.items);
    if (page.items.length < 100) return result;
  }
}
