"""
Desconecta todos os bots (Telegram e WhatsApp/Evolution) no banco da plataforma.
Uso: na raiz do projeto, com .env carregado:
  python execution/disconnect_all_bots.py
"""
import os
import sys

# raiz do projeto
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# carrega .env
try:
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(ROOT) / ".env", override=True)
except ImportError:
    pass


def main():
    from platform_backend.db import get_cursor
    from platform_backend.whatsapp_crypto import decrypt_token

    import httpx

    def delete_telegram_webhook(token: str) -> bool:
        try:
            r = httpx.get(f"https://api.telegram.org/bot{token}/deleteWebhook", timeout=10.0)
            return r.json().get("ok", False)
        except Exception:
            return False

    with get_cursor() as cur:
        # Telegram: remover webhook de cada bot e depois apagar config
        cur.execute(
            "SELECT tenant_id, bot_token_encrypted FROM tenant_telegram_config"
        )
        telegram_rows = cur.fetchall()
    for row in telegram_rows:
        try:
            token = decrypt_token(row["bot_token_encrypted"])
            ok = delete_telegram_webhook(token)
            print(f"Telegram tenant {row['tenant_id']}: deleteWebhook ok={ok}")
        except Exception as e:
            print(f"Telegram tenant {row['tenant_id']}: erro ao remover webhook: {e}")
        # mesmo com erro, vamos apagar o registro

    tg = wa = ev = 0
    with get_cursor() as cur:
        cur.execute("DELETE FROM tenant_telegram_config")
        tg = cur.rowcount
    with get_cursor() as cur:
        try:
            cur.execute("DELETE FROM tenant_whatsapp_config")
            wa = cur.rowcount
        except Exception as e:
            if "does not exist" in str(e):
                wa = 0
            else:
                raise
    with get_cursor() as cur:
        try:
            cur.execute("DELETE FROM tenant_evolution_config")
            ev = cur.rowcount
        except Exception as e:
            if "does not exist" in str(e):
                ev = 0
            else:
                raise

    print(f"Pronto. Removidos: Telegram={tg}, WhatsApp={wa}, Evolution={ev}.")


if __name__ == "__main__":
    main()
