"""
Camada 3 - Execução: máquina de estados SPIN.
Transições apenas sequenciais; nunca pular etapas.
"""

from .db_sessions import STATES

# Ordem canônica para validar avanço
STATE_ORDER = list(STATES)


def get_next_state(current: str) -> str | None:
    """Retorna o próximo estado na sequência, ou None se já estiver no último."""
    try:
        i = STATE_ORDER.index(current)
        if i + 1 < len(STATE_ORDER):
            return STATE_ORDER[i + 1]
        return None
    except ValueError:
        return None


def can_transition(current: str, proposed: str) -> bool:
    """
    Verifica se a transição de current para proposed é permitida.
    Regras: só avanço sequencial (um passo) ou permanecer no mesmo estado.
    Não permite pular etapas nem voltar (exceto pos_venda que pode ser reentrado após fechamento).
    """
    if current == proposed:
        return True
    if proposed not in STATE_ORDER or current not in STATE_ORDER:
        return False
    curr_i = STATE_ORDER.index(current)
    prop_i = STATE_ORDER.index(proposed)
    # Avanço de exatamente um passo
    if prop_i == curr_i + 1:
        return True
    # Permite ir para pos_venda a partir de fechamento (próximo lógico)
    if current == "fechamento" and proposed == "pos_venda":
        return True
    return False


def apply_transition(current: str, proposed: str) -> str:
    """
    Se a transição for válida, retorna o novo estado (proposed).
    Caso contrário, retorna current (não altera).
    """
    if can_transition(current, proposed):
        return proposed
    return current


def get_state_display_name(state: str) -> str:
    """Nome legível do estado para uso em prompts."""
    names = {
        "descoberta": "Descoberta (Situation)",
        "problema": "Problema (Problem)",
        "implicacao": "Implicação (Implication)",
        "solucao": "Solução (Need Payoff)",
        "oferta": "Oferta",
        "fechamento": "Fechamento",
        "pos_venda": "Pós-venda",
    }
    return names.get(state, state)
