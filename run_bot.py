#!/usr/bin/env python3
"""
Ponto de entrada do bot SDR Telegram.
Execute: python run_bot.py (dev) ou python run_production.py (produção com reinício).
Modo produção: RUN_MODE=production no .env — log em arquivo + nível INFO.
"""

import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# Logging: produção = arquivo .tmp/logs/bot.log + console, nível INFO
RUN_MODE = os.environ.get("RUN_MODE", "").strip().lower()
IS_PRODUCTION = RUN_MODE == "production"
if IS_PRODUCTION:
    log_dir = Path(os.environ.get("LOG_DIR", "")).expanduser() or (ROOT / ".tmp" / "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "bot.log"
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.getLogger().info("Modo produção — log em %s", log_file)
else:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

redis_url = os.environ.get("REDIS_URL", "").strip()
if redis_url:
    try:
        import redis
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
        debounce = os.environ.get("MESSAGE_BUFFER_DEBOUNCE_SECONDS", "5").strip()
        print(f"Buffer ativo (Redis OK). Debounce: {debounce}s — mensagens serão agrupadas antes de responder.")
    except Exception as e:
        print(f"AVISO: Redis indisponível ({e}). Mensagens serão respondidas uma a uma. Para TLS (Redis Labs), use rediss:// no REDIS_URL.")

from execution.telegram_handler import run_bot

if __name__ == "__main__":
    run_bot()
