#!/usr/bin/env python3
"""
Platform Backend (FastAPI) em modo produção.
- Sem reload (estável, menos uso de memória).
- Host/porta por variáveis de ambiente (útil em Railway, Render, VPS).
- Log em nível INFO.

Uso:
  python run_platform_backend_production.py

Variáveis opcionais:
  PLATFORM_HOST=0.0.0.0   (aceitar conexões externas)
  PLATFORM_PORT=8000
  LOG_LEVEL=INFO
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Carregar .env antes de importar o app
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=True)
except ImportError:
    pass

def main():
    import uvicorn
    host = os.environ.get("PLATFORM_HOST", "0.0.0.0")
    port = int(os.environ.get("PLATFORM_PORT", "8000"))
    log_level = os.environ.get("LOG_LEVEL", "info").lower()
    uvicorn.run(
        "platform_backend.main:app",
        host=host,
        port=port,
        reload=False,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
