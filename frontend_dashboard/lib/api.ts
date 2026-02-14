const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";
export function getApiBase(): string {
  return API_BASE;
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

  const url = `${API_BASE}${path}`;
  let res: Response;
  try {
    res = await fetch(url, { ...options, headers });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "";
    if (msg === "Failed to fetch" || (e instanceof TypeError && msg.toLowerCase().includes("fetch"))) {
      throw new Error(
        "Não foi possível conectar ao servidor. Verifique se o backend está rodando (python run_platform_backend.py) em http://127.0.0.1:8000 e teste http://127.0.0.1:8000/health no navegador."
      );
    }
    throw e;
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail) && detail.length > 0
          ? (detail[0].msg ?? detail[0].message ?? JSON.stringify(detail[0]))
          : String(res.status);
    throw new Error(msg);
  }
  return res.json();
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
