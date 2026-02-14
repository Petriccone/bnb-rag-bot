# Regras de planos e billing

## Planos
- **free**: 1 agente, 500 mensagens/mês.
- **pro**: 5 agentes, 10.000 mensagens/mês.
- **enterprise**: agentes e mensagens ilimitados.

## Verificação
- Usar `execution/plan_limit_checker.py`: `check_agent_limit(tenant_id)` antes de criar agente; `check_message_limit(tenant_id)` antes de processar mensagem (opcional no core ou no platform ao receber webhook).
- Rate limit por plano: aplicar no platform_backend ao expor APIs.

## Atualização de plano
- Alterar campo `tenants.plan` apenas pela plataforma (dashboard/admin).
- Não permitir downgrade que viole limites atuais (ex.: remover agente antes de mudar para free).
