#!/usr/bin/env python3
"""
Runner em modo produção: inicia o bot e reinicia automaticamente em caso de queda.
Ativa log em arquivo (.tmp/logs/bot.log) e nível INFO.
Uso: python run_production.py
"""

import logging
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["RUN_MODE"] = "production"
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# Log em arquivo + console (produção)
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
logger = logging.getLogger(__name__)
logger.info("Modo produção — log em %s. Reinício automático em caso de queda.", log_file)

from execution.telegram_handler import run_bot

RESTART_DELAY_SECONDS = 10


def main():
    while True:
        try:
            run_bot()
        except KeyboardInterrupt:
            logger.info("Encerramento solicitado (Ctrl+C).")
            sys.exit(0)
        except Exception as e:
            logger.exception("Bot encerrou com erro. Reiniciando em %ss...", RESTART_DELAY_SECONDS)
            time.sleep(RESTART_DELAY_SECONDS)


if __name__ == "__main__":
    main()
