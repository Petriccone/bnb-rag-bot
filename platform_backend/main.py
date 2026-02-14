"""
Platform Backend (SaaS) — FastAPI.
Autenticação JWT, CRUD tenant/agentes, upload documentos, métricas, WhatsApp (stub).
Consumido apenas pelo frontend_dashboard; o core não chama o platform.
"""
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


@asynccontextmanager
async def lifespan(app):
    """Inicia worker do buffer (webhook Telegram) se REDIS_URL estiver definido."""
    from .webhook_buffer import start_worker_if_needed
    start_worker_if_needed()
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


@app.get("/health")
def health():
    return {"status": "ok"}
