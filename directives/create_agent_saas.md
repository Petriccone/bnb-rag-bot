# Criação e edição de agente (SaaS)

## Objetivo
Permitir que o tenant crie e edite agentes SDR na plataforma, com customização de prompt sem remover SPIN.

## Regras obrigatórias
- SPIN Selling é obrigatório para todos os agentes. O usuário pode customizar prompt (personalidade, nicho), mas **não** pode remover as etapas SPIN nem a ordem dos estados.
- Cada agente pertence a um tenant (`tenant_id`).
- Campos: name, niche, prompt_custom (texto livre que será mesclado ou usado junto às diretivas SPIN), active.
- Antes de criar agente, verificar limite do plano (plan_limit_checker.check_agent_limit).

## Fluxo de criação
1. Verificar se tenant pode criar mais um agente (plano free = 1, pro = 5, enterprise = ilimitado).
2. Inserir em `agents` com tenant_id, name, niche, prompt_custom, active=true.
3. Retornar id do agente.

## Customização de prompt
- prompt_custom pode conter instruções adicionais (ex.: "Foco em filtros para apartamento").
- O sistema sempre injeta as diretivas SPIN e sdr_personalidade; o prompt_custom complementa, não substitui.
