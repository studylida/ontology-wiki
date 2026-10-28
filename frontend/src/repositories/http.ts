import { authStorage, AUTH_CHANGED } from './workspaceStorage';
export { authStorage } from './workspaceStorage';
const API = import.meta.env.VITE_API_BASE_URL || '/api/v1';
export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string,
    public retryable = false, public details?: unknown) { super(message); this.name = 'ApiError'; }
}
export const errorMessage = (error: unknown) => error instanceof Error ? error.message : '요청을 처리하지 못했습니다.';
export const isAbort = (error: unknown) => error instanceof DOMException && error.name === 'AbortError';
export const apiUrl = (path: string) => `${API}${path}`;
export function requestHeaders(json = false): Headers {
  const headers = new Headers({ Accept: 'application/json' });
  const token = authStorage.getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (json) headers.set('Content-Type', 'application/json');
  return headers;
}
export async function responseError(response: Response): Promise<ApiError> {
  let body: { error?: { code?: string; message?: string; retryable?: boolean; details?: unknown }; detail?: unknown } = {};
  try { body = await response.json(); } catch { /* Never render HTML error pages. */ }
  if (response.status === 401 && authStorage.getToken()) window.dispatchEvent(new Event(AUTH_CHANGED));
  return new ApiError(response.status, body.error?.code || `HTTP_${response.status}`,
    body.error?.message || (typeof body.detail === 'string' ? body.detail : `요청을 처리하지 못했습니다 (${response.status}).`),
    body.error?.retryable ?? response.status >= 500, body.error?.details);
}
export async function http<T>(path: string, options: { method?: string; body?: unknown; signal?: AbortSignal; binary?: boolean } = {}): Promise<T> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  options.signal?.addEventListener('abort', abort, { once: true });
  if (options.signal?.aborted) controller.abort();
  const timeout = setTimeout(abort, 60000);
  try {
    const multipart = options.body instanceof FormData;
    const response = await fetch(apiUrl(path), { method: options.method || 'GET',
      headers: requestHeaders(options.body !== undefined && !multipart),
      body: options.body === undefined ? undefined : multipart ? options.body as FormData : JSON.stringify(options.body),
      signal: controller.signal, cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw await responseError(response);
    if (response.status === 204) return undefined as T;
    return options.binary ? await response.blob() as T : await response.json();
  } catch (error) {
    if (error instanceof ApiError || options.signal?.aborted) throw error;
    throw new ApiError(0, 'NETWORK_UNAVAILABLE', '서버 응답을 확인하지 못했습니다. 접수 여부를 확인한 뒤 같은 요청으로 다시 전송해 주세요.', true);
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener('abort', abort);
  }
}
export async function downloadSource(documentId: string, revisionId: string) {
  const blob = await http<Blob>(`/documents/${encodeURIComponent(documentId)}/raw?revisionId=${encodeURIComponent(revisionId)}`, { binary: true });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  const extension = blob.type.includes('pdf') ? '.pdf' : blob.type.includes('xml') ? '.xml' : blob.type.includes('markdown') ? '.md' : '.txt';
  link.download = `source-${documentId}-${revisionId}${extension}`;
  document.body.append(link);
  link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
