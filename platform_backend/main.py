"""
Platform Backend (SaaS) — FastAPI.
Autenticação JWT, CRUD tenant/agentes, upload documentos, métricas, WhatsApp (stub).
Consumido apenas pelo frontend_dashboard; o core não chama o platform.
"""
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path, override=True)
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, tenants, agents, documents, metrics, whatsapp, telegram, telegram_webhook

# #region agent log
def _debug_log(message: str, data: dict, hypothesis_id: str = ""):
    try:
        root = Path(__file__).resolve().parent.parent
        log_path = root / ".cursor" / "debug.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"message": message, "data": data, "hypothesisId": hypothesis_id, "timestamp": __import__("time").time() * 1000}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion


@asynccontextmanager
async def lifespan(app):
    """Inicia worker do buffer (webhook Telegram) se REDIS_URL estiver definido."""
    # #region agent log
    _debug_log("lifespan_start", {"db_set": bool(os.environ.get("DATABASE_URL") or os.environ.get("PLATFORM_DATABASE_URL")), "redis_set": bool(os.environ.get("REDIS_URL"))}, "H1")
    # #endregion
    try:
        from .webhook_buffer import start_worker_if_needed
        start_worker_if_needed()
    except Exception:
        pass
    yield


app = FastAPI(title="B&B RAG Platform API", version="1.0.0", lifespan=lifespan)

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
    # #region agent log
    _debug_log("root_hit", {"path": "/"}, "H2")
    # #endregion
    return {
        "message": "B&B RAG Platform API",
        "docs": "/docs",
        "health": "/health",
        "api": "/api",
    }


@app.get("/health")
def health():
    # #region agent log
    _debug_log("health_hit", {"path": "/health"}, "H2")
    # #endregion
    return {"status": "ok"}
