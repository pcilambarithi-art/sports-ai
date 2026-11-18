const TOKEN_KEY = 'apexpulse_jwt_token';
const API_BASE_KEY = 'apexpulse_api_base';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getApiBaseUrl(): string {
  const saved = localStorage.getItem(API_BASE_KEY);
  if (saved && saved.trim()) {
    return saved.trim().replace(/\/+$/, '');
  }
  const envBase = (import.meta as any).env?.VITE_API_BASE_URL || '';
  return String(envBase).trim().replace(/\/+$/, '');
}

export function setApiBaseUrl(url: string): void {
  const clean = url.trim().replace(/\/+$/, '');
  if (clean) {
    localStorage.setItem(API_BASE_KEY, clean);
  } else {
    localStorage.removeItem(API_BASE_KEY);
  }
}

export function isGitHubPagesHost(): boolean {
  return typeof window !== 'undefined' && window.location.hostname.endsWith('github.io');
}

export function resolveApiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  const base = getApiBaseUrl();
  if (!base) return path;
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData) && !headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json');
  }

  const fullUrl = resolveApiUrl(path);
  let res: Response;
  try {
    res = await fetch(fullUrl, {
      ...options,
      headers,
    });
  } catch {
    throw new ApiError(
      isGitHubPagesHost() && !getApiBaseUrl()
        ? 'GitHub Pages hosts the static frontend only. Enter your live Backend Server URL (Cloudflare Tunnel / Railway / VPS) in Backend Connection Settings.'
        : `Cannot reach backend server (${fullUrl}). Verify the FastAPI backend is running.`,
      0
    );
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    if (res.status === 405 || (isGitHubPagesHost() && !getApiBaseUrl() && res.status === 404)) {
      throw new ApiError(
        'GitHub Pages cannot execute Python API routes directly. Click "Backend Server URL" below and paste your live Cloudflare Tunnel or Railway backend URL.',
        res.status
      );
    }
    if (res.status >= 502 && res.status <= 504) {
      throw new ApiError(
        `Backend server is restarting or temporarily unreachable (HTTP ${res.status}). Please retry in a few seconds.`,
        res.status
      );
    }
    const rawDetail =
      (data && typeof data === 'object' && (data.detail || data.message)) ||
      (typeof data === 'string' && !data.trim().startsWith('<') ? data : null) ||
      `Request failed (HTTP ${res.status})`;
    const msg = Array.isArray(rawDetail)
      ? rawDetail.map((d: any) => d.msg || JSON.stringify(d)).join('; ')
      : String(rawDetail);
    throw new ApiError(msg, res.status);
  }

  return data as T;
}

export async function downloadCsv(path: string, filename: string): Promise<void> {
  const token = getStoredToken();
  const res = await fetch(resolveApiUrl(path), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new ApiError('Failed to export CSV data.', res.status);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function buildWsUrl(path: string): string {
  const base = getApiBaseUrl();
  if (base) {
    const wsBase = base.replace(/^https:\/\//i, 'wss://').replace(/^http:\/\//i, 'ws://');
    return `${wsBase}${path.startsWith('/') ? path : `/${path}`}`;
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${path}`;
}
