# Message Buffer com Debounce Inteligente

## Objetivo do buffer

Consolidar múltiplas mensagens enviadas em sequência pelo usuário em uma única entrada para o CORE, evitando comportamento robótico (várias respostas seguidas). O buffer aguarda uma janela de tempo, junta as mensagens e dispara **uma única** chamada ao agente.

## Janela padrão

- **3 segundos**: janela padrão de espera após a última mensagem antes de consolidar e chamar o agente.
- Nunca permitir espera superior a **5 segundos**.

## Regras de timeout (debounce inteligente)

- **Mensagem &lt; 10 caracteres** ou **sem pontuação no final** → aumentar espera para **4 segundos** (usuário pode estar ainda digitando).
- **Mensagem &gt; 200 caracteres** → responder em **1,5 segundos** (mensagem já completa).
- **Máximo**: 5 segundos; **mínimo** sugerido: 1,5 s quando mensagem longa.

## Edge cases

| Caso | Regra |
|------|--------|
| Mensagens muito longas | Tratar como mensagem completa; debounce curto (1,5 s). |
| Mensagem com interrogação | Considerar possível fim de turno; não aumentar demais a janela. |
| Usuário digitando continuamente | Várias mensagens curtas sem pontuação → usar 4 s para dar tempo de “parar de digitar”. |
| Apenas uma mensagem | Após a janela (3–4 s), consolidar “uma única mensagem” e enviar ao CORE normalmente. |

## Regras multi-tenant

- Buffer **isolado por tenant**: chave Redis `buffer:{tenant_id}:{user_id}`.
- Um tenant não enxerga o buffer de outro.
- Suportar 2.000+ tenants sem acoplamento (chave composta, sem estado global).

## Regras por user_id

- Dentro do mesmo tenant, cada **user_id** tem seu próprio buffer e seu próprio temporizador.
- Resetar o temporizador a cada nova mensagem do mesmo usuário.

## Self-annealing em caso de falha no Redis

- Se Redis estiver indisponível ou der erro ao escrever/ler o buffer:
  - **Não travar** o fluxo: fallback para processar a mensagem atual **sem buffer** (enviar direto ao CORE).
  - Registrar log de falha e, se houver diretiva de retry, tentar reconectar/retentar em background.
  - Não bloquear a thread principal; o usuário sempre recebe resposta (com ou sem consolidação).

## Onde o buffer atua

- A consolidação ocorre na **camada de adapters**, **antes** de chamar o CORE (run_agent).
- O CORE recebe **apenas texto já consolidado**; não contém lógica de buffer.
