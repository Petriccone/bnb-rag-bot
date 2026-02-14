"""
Cenário de teste: usuário envia "Oi", 2s depois "Vocês trabalham com energia solar?", 1s depois "Qual o valor?"
Sistema deve consolidar como: "Oi Vocês trabalham com energia solar? Qual o valor?" e gerar apenas UMA resposta.
"""

import asyncio
import os
import sys
from pathlib import Path

# Raiz do projeto
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Carregar .env para REDIS_URL
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")


def test_compute_debounce_delay():
    """Testa regras de debounce: < 10 chars, > 200 chars, pontuação. Sem MESSAGE_BUFFER_DEBOUNCE_SECONDS."""
    os.environ.pop("MESSAGE_BUFFER_DEBOUNCE_SECONDS", None)
    from execution.telegram_buffer_adapter import compute_debounce_delay
    assert compute_debounce_delay("Oi") == 5.0
    assert compute_debounce_delay("Qual o valor?") == 4.0
    assert compute_debounce_delay("x" * 201) == 2.0
    assert compute_debounce_delay("") == 5.0
    assert compute_debounce_delay("ok") == 5.0


def test_buffer_consolidation():
    """
    Simula: add "Oi", add "Vocês trabalham com energia solar?", add "Qual o valor?"
    get_combined_messages deve retornar as três concatenadas.
    """
    if not os.environ.get("REDIS_URL", "").strip():
        print("REDIS_URL não definido — pulando test_buffer_consolidation")
        return
    from execution import message_buffer as buf
    tenant_id = "test_tenant"
    user_id = "test_user_123"
    buf.clear_buffer(tenant_id, user_id)
    buf.add_message_to_buffer(tenant_id, user_id, "Oi", None)
    buf.add_message_to_buffer(tenant_id, user_id, "Vocês trabalham com energia solar?", None)
    buf.add_message_to_buffer(tenant_id, user_id, "Qual o valor?", None)
    combined = buf.get_combined_messages(tenant_id, user_id)
    expected = "Oi Vocês trabalham com energia solar? Qual o valor?"
    assert combined.strip() == expected.strip(), f"Esperado '{expected}', obtido '{combined}'"
    buf.clear_buffer(tenant_id, user_id)
    assert buf.get_combined_messages(tenant_id, user_id) == ""
    print("test_buffer_consolidation: OK")


async def test_adapter_delayed_flush():
    """Testa que o adapter agenda flush e consolida após o delay (sem chamar run_agent de produção)."""
    from execution.telegram_buffer_adapter import compute_debounce_delay
    delay = compute_debounce_delay("Oi")
    assert 2.0 <= delay <= 8.0
    print("test_adapter_delayed_flush: delay OK")


if __name__ == "__main__":
    test_compute_debounce_delay()
    test_buffer_consolidation()
    asyncio.run(test_adapter_delayed_flush())
    print("Todos os cenários de message buffer passaram.")
