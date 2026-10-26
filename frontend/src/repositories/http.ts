const TOKEN_KEY = "knowledge-hub.session";
const API = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public retryable = false,
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export const authStorage = {
  getToken(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  },
  setToken(token: string) {
    sessionStorage.setItem(TOKEN_KEY, token);
  },
  clear() {
    sessionStorage.removeItem(TOKEN_KEY);
  },
};
export function apiUrl(path: string) {
  return `${API}${path}`;
}
export function requestHeaders(json = false): Headers {
  const headers = new Headers({ Accept: "application/json" });
  const token = authStorage.getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (json) headers.set("Content-Type", "application/json");
  return headers;
}
export async function responseError(response: Response): Promise<ApiError> {
  let body: {
    error?: {
      code?: string;
      message?: string;
      retryable?: boolean;
      details?: unknown;
    };
    detail?: string;
  } = {};
  try {
    body = await response.json();
  } catch {
    /* Never display an HTML error body or request credentials. */
  }
  return new ApiError(
    response.status,
    body.error?.code || `HTTP_${response.status}`,
    body.error?.message ||
      (typeof body.detail === "string"
        ? body.detail
        : `요청을 처리하지 못했습니다 (${response.status}).`),
    body.error?.retryable ?? response.status >= 500,
    body.error?.details,
  );
}
export async function http<T>(
  path: string,
  options: { method?: string; body?: unknown; signal?: AbortSignal } = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      method: options.method || "GET",
      headers: requestHeaders(options.body !== undefined),
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
      cache: "no-store",
      credentials: "same-origin",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    throw new ApiError(
      0,
      "NETWORK_UNAVAILABLE",
      "서버에 연결하지 못했습니다. 연결을 확인한 뒤 다시 시도해 주세요.",
      true,
    );
  }
  if (!response.ok) throw await responseError(response);
  if (response.status === 204) return undefined as T;
  return response.json();
}
export const errorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : "요청을 처리하지 못했습니다.";
export const isAbort = (error: unknown): boolean =>
  error instanceof DOMException && error.name === "AbortError";
