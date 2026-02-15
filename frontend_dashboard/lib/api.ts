/**
 * Base da API (termina em /api).
 * Em produção: use NEXT_PUBLIC_API_URL = URL da API (chamada direta, evita 405 do proxy).
 * Desenvolvimento: mesma origem ou http://127.0.0.1:8000.
 */
function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  const raw =
    envUrl ||
    (typeof window !== "undefined" ? window.location.origin : "") ||
    "http://127.0.0.1:8000";
  const base = String(raw).replace(/\/+$/, "");
  return base.endsWith("/api") ? base : base + "/api";
}
export function getApiBase(): string {
  return getApiBaseUrl();
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;

  const base = getApiBaseUrl().replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  const apiPath = "/api" + (p.startsWith("/") ? p : `/${p}`);
  (headers as Record<string, string>)["X-Request-Path"] = apiPath;
  const sep = base.includes("?") ? "&" : "?";
  const url = `${base}${p}${sep}_path=${encodeURIComponent(apiPath)}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);
  let res: Response;
  try {
    res = await fetch(url, { ...options, headers, signal: controller.signal });
  } catch (e) {
    clearTimeout(timeoutId);
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error("A requisição demorou muito. Tente novamente.");
    }
    const msg = e instanceof Error ? e.message : "";
    if (msg === "Failed to fetch" || (e instanceof TypeError && msg.toLowerCase().includes("fetch"))) {
      const hint = typeof window !== "undefined" && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost"
        ? " No projeto do dashboard (Vercel), defina BACKEND_URL com a URL da API (ex.: https://bnb-rag-api.vercel.app) e faça redeploy."
        : " Verifique se o backend está rodando (python run_platform_backend.py) e teste /health no navegador.";
      throw new Error("Não foi possível conectar à API." + hint);
    }
    throw e;
  }
  clearTimeout(timeoutId);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail ?? err.message ?? err.error;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail) && detail.length > 0
          ? (detail[0].msg ?? detail[0].message ?? JSON.stringify(detail[0]))
          : String(detail ?? res.status);
    const fullMsg = (msg && String(msg).trim()) ? msg : `Erro do servidor (${res.status})`;
    throw new Error(fullMsg);
  }
  const text = await res.text();
  if (!text || !text.trim()) {
    throw new Error("Resposta vazia do servidor.");
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(text) as T;
  } catch {
    throw new Error("Resposta inválida do servidor (não é JSON).");
  }
  return parsed as T;
}

export function setToken(token: string) {
  if (typeof window !== "undefined") localStorage.setItem("token", token);
}

export function clearToken() {
  if (typeof window !== "undefined") localStorage.removeItem("token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
