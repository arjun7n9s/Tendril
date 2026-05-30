/**
 * Tendril API client.
 *
 * Thin fetch wrapper around the FastAPI backend. Centralizes:
 * - base URL handling via NEXT_PUBLIC_API_BASE_URL,
 * - JSON parsing,
 * - error normalization into ApiError,
 * - request timeouts (default 20s, longer for CSV uploads).
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  code: string;
  detail?: unknown;

  constructor(status: number, code: string, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

type QueryValue = string | number | boolean | null | undefined;
type QueryParams = Record<string, QueryValue>;

function buildUrl(path: string, params?: QueryParams): string {
  const url = new URL(path.startsWith("http") ? path : `${API_BASE_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

export type RequestOptions = {
  params?: QueryParams;
  body?: unknown;
  formData?: FormData;
  signal?: AbortSignal;
  timeoutMs?: number;
  headers?: Record<string, string>;
  cache?: RequestCache;
};

async function request<T>(
  method: string,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { params, body, formData, signal, timeoutMs = 20_000, headers, cache } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", () => controller.abort());
  }

  let payload: BodyInit | undefined;
  const finalHeaders: Record<string, string> = {
    Accept: "application/json",
    // Bypass ngrok's free-tier browser interstitial so we always get JSON
    // back from the API rather than ngrok's HTML warning page. Harmless on
    // non-ngrok backends (unknown request headers are ignored).
    "ngrok-skip-browser-warning": "true",
    ...(headers ?? {}),
  };
  if (formData) {
    payload = formData;
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    finalHeaders["Content-Type"] = "application/json";
  }

  let res: Response;
  try {
    res = await fetch(buildUrl(path, params), {
      method,
      headers: finalHeaders,
      body: payload,
      signal: controller.signal,
      cache: cache ?? "no-store",
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (controller.signal.aborted) {
      throw new ApiError(0, "timeout", "Request timed out");
    }
    if (err instanceof Error) {
      throw new ApiError(0, "network", err.message);
    }
    throw new ApiError(0, "network", "Network error");
  } finally {
    clearTimeout(timeoutId);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  let parsed: unknown = null;
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    parsed = await res.json().catch(() => null);
  } else {
    const text = await res.text().catch(() => "");
    parsed = text ? { message: text } : null;
  }

  if (!res.ok) {
    const detail =
      parsed && typeof parsed === "object" && "detail" in parsed
        ? (parsed as { detail: unknown }).detail
        : parsed;
    const code =
      typeof detail === "string"
        ? detail
        : typeof detail === "object" && detail && "code" in detail
          ? String((detail as { code: unknown }).code)
          : `http_${res.status}`;
    const message =
      typeof detail === "string"
        ? detail
        : typeof detail === "object" && detail && "message" in detail
          ? String((detail as { message: unknown }).message)
          : res.statusText || "Request failed";
    throw new ApiError(res.status, code, message, parsed);
  }

  return parsed as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) => request<T>("GET", path, options),
  post: <T>(path: string, options?: RequestOptions) => request<T>("POST", path, options),
  patch: <T>(path: string, options?: RequestOptions) => request<T>("PATCH", path, options),
  put: <T>(path: string, options?: RequestOptions) => request<T>("PUT", path, options),
  delete: <T>(path: string, options?: RequestOptions) => request<T>("DELETE", path, options),
};
