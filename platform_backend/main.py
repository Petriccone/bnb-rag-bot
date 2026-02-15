"""
Platform Backend (SaaS) — FastAPI.
Autenticação JWT, CRUD tenant/agentes, upload documentos, métricas, WhatsApp (stub).
Consumido apenas pelo frontend_dashboard; o core não chama o platform.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path, override=True)
except ImportError:
    pass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, tenants, agents, documents, metrics, whatsapp, telegram, telegram_webhook


def _normalize_api_path(raw: str) -> str:
    if not raw or not raw.startswith("/"):
        return ""
    return raw if raw.startswith("/api") else "/api" + raw


class VercelPathFixMiddleware(BaseHTTPMiddleware):
    """Na Vercel o path chega como "/". Corrige com header X-Request-Path, query _path ou prefixo /api."""
    async def dispatch(self, request, call_next):
        path = request.scope.get("path") or ""
        method = request.scope.get("method") or ""
        # #region agent log — debug 405: retorna o que o servidor recebeu (path, query, header)
        if path in ("/", "/index.py") and method == "POST":
            q = request.query_params
            debug_payload = {
                "debug": True,
                "hypothesisId": "H1,H5",
                "scope_path": path,
                "method": method,
                "query_path": q.get("_path"),
                "query_path_alt": q.get("path"),
                "header_x_request_path": request.headers.get("x-request-path"),
                "query_keys": list(q.keys()),
            }
            try:
                import json
                root = Path(__file__).resolve().parent.parent
                log_path = root / ".cursor" / "debug.log"
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"message": "vercel_debug", "data": debug_payload, "timestamp": __import__("time").time() * 1000}) + "\n")
            except Exception:
                pass
            return JSONResponse(status_code=200, content=debug_payload)
        # #endregion
        fixed = ""
        if path in ("/", "/index.py") and method != "GET":
            fixed = _normalize_api_path(request.headers.get("x-request-path") or "")
            if not fixed:
                fixed = _normalize_api_path(request.query_params.get("_path") or request.query_params.get("path") or "")
        if fixed:
            request.scope["path"] = fixed
        elif path and not path.startswith("/api") and path not in ("/", "/health"):
            if any(path.startswith(x) for x in ("/auth", "/webhook", "/tenants", "/agents", "/documents", "/metrics", "/docs")):
                request.scope["path"] = "/api" + path
        return await call_next(request)


@asynccontextmanager
async def lifespan(app):
    """Inicia worker do buffer (webhook Telegram) se REDIS_URL estiver definido."""
    try:
        from .webhook_buffer import start_worker_if_needed
        start_worker_if_needed()
    except Exception:
        pass
    yield


app = FastAPI(title="B&B RAG Platform API", version="1.0.0", lifespan=lifespan)

app.add_middleware(VercelPathFixMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(tenants.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")
app.include_router(telegram.router, prefix="/api")
app.include_router(telegram_webhook.router, prefix="/api/webhook/telegram")


@app.get("/")
def root():
    """Rota raiz: evita 404 ao abrir a URL da API no navegador."""
    return {
        "message": "B&B RAG Platform API",
        "docs": "/docs",
        "health": "/health",
        "api": "/api",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
