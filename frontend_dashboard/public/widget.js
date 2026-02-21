/**
 * Botfy Web Widget — Embeddable AI Chat
 * Embed: <script src="https://your-api.railway.app/api/widget/widget.js"
 *           data-agent-id="AGENT_ID"
 *           data-tenant-id="TENANT_ID"
 *           data-color="#2563EB"
 *           data-position="right">
 *         </script>
 *
 * Or initialize manually:
 *   BotfyWidget.init({ agentId, tenantId, apiUrl, color, position });
 */
(function () {
    'use strict';

    const DEFAULT_API = 'https://your-api.railway.app/api';
    const SESSION_KEY = 'botfy_session_id';

    function getOrCreateSession() {
        let sid = sessionStorage.getItem(SESSION_KEY);
        if (!sid) {
            sid = Math.random().toString(36).slice(2) + Date.now().toString(36);
            sessionStorage.setItem(SESSION_KEY, sid);
        }
        return sid;
    }

    function injectStyles(color, position) {
        const css = `
      #botfy-widget-btn {
        position: fixed;
        bottom: 24px;
        ${position === 'left' ? 'left: 24px;' : 'right: 24px;'}
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: ${color};
        color: white;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        z-index: 999998;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s, box-shadow 0.2s;
        font-size: 24px;
      }
      #botfy-widget-btn:hover { transform: scale(1.08); box-shadow: 0 6px 28px rgba(0,0,0,0.3); }
      #botfy-widget-container {
        position: fixed;
        bottom: 92px;
        ${position === 'left' ? 'left: 24px;' : 'right: 24px;'}
        width: 360px;
        height: 520px;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 40px rgba(0,0,0,0.3);
        z-index: 999999;
        display: none;
        flex-direction: column;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: #0f1117;
        border: 1px solid #1f2937;
      }
      #botfy-widget-container.open { display: flex; }
      #botfy-header {
        background: ${color};
        padding: 14px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-shrink: 0;
      }
      #botfy-header-info { display: flex; align-items: center; gap: 10px; }
      #botfy-avatar {
        width: 36px; height: 36px;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 18px;
      }
      #botfy-agent-name { color: white; font-weight: 700; font-size: 14px; }
      #botfy-agent-niche { color: rgba(255,255,255,0.75); font-size: 11px; margin-top: 1px; }
      #botfy-close-btn {
        background: none; border: none; cursor: pointer;
        color: rgba(255,255,255,0.75); font-size: 20px; line-height: 1;
        padding: 0; transition: color 0.15s;
      }
      #botfy-close-btn:hover { color: white; }
      #botfy-messages {
        flex: 1; overflow-y: auto; padding: 16px; display: flex;
        flex-direction: column; gap: 12px; background: #0b0e14;
      }
      .botfy-msg { display: flex; align-items: flex-end; gap: 8px; }
      .botfy-msg.user { flex-direction: row-reverse; }
      .botfy-bubble {
        max-width: 80%; padding: 10px 14px; border-radius: 18px;
        font-size: 13px; line-height: 1.5; word-break: break-word;
      }
      .botfy-msg.bot .botfy-bubble {
        background: #1f2937; color: #f3f4f6;
        border-bottom-left-radius: 4px;
      }
      .botfy-msg.user .botfy-bubble {
        background: ${color}; color: white;
        border-bottom-right-radius: 4px;
      }
      .botfy-typing { display: flex; gap: 4px; padding: 12px 14px; }
      .botfy-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: #6b7280; animation: botfy-bounce 1s infinite;
      }
      .botfy-dot:nth-child(2) { animation-delay: 0.15s; }
      .botfy-dot:nth-child(3) { animation-delay: 0.3s; }
      @keyframes botfy-bounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-6px); }
      }
      #botfy-input-area {
        padding: 12px; display: flex; gap: 8px;
        background: #0f1117; border-top: 1px solid #1f2937; flex-shrink: 0;
      }
      #botfy-input {
        flex: 1; background: #1f2937; border: 1px solid #374151;
        color: white; padding: 10px 14px; border-radius: 12px;
        font-size: 13px; outline: none;
      }
      #botfy-input::placeholder { color: #6b7280; }
      #botfy-send {
        background: ${color}; color: white; border: none;
        padding: 10px 14px; border-radius: 12px; cursor: pointer;
        font-size: 16px; transition: opacity 0.2s;
      }
      #botfy-send:disabled { opacity: 0.4; cursor: not-allowed; }
      #botfy-branding {
        text-align: center; font-size: 10px; color: #4b5563;
        padding: 4px 0 8px; flex-shrink: 0; background: #0f1117;
      }
      #botfy-branding a { color: #6b7280; text-decoration: none; }
    `;
        const el = document.createElement('style');
        el.textContent = css;
        document.head.appendChild(el);
    }

    function buildWidget(config) {
        const { agentId, tenantId, apiUrl, agentName, agentNiche, color, position } = config;
        injectStyles(color, position);

        // Floating button
        const btn = document.createElement('button');
        btn.id = 'botfy-widget-btn';
        btn.innerHTML = '💬';
        btn.title = 'Abrir chat';

        // Container
        const container = document.createElement('div');
        container.id = 'botfy-widget-container';

        container.innerHTML = `
      <div id="botfy-header">
        <div id="botfy-header-info">
          <div id="botfy-avatar">🤖</div>
          <div>
            <div id="botfy-agent-name">${agentName}</div>
            ${agentNiche ? `<div id="botfy-agent-niche">${agentNiche}</div>` : ''}
          </div>
        </div>
        <button id="botfy-close-btn">✕</button>
      </div>
      <div id="botfy-messages"></div>
      <div id="botfy-input-area">
        <input id="botfy-input" type="text" placeholder="Digite sua mensagem..." />
        <button id="botfy-send">➤</button>
      </div>
      <div id="botfy-branding">Powered by <a href="https://botfy.ai" target="_blank">Botfy</a></div>
    `;

        document.body.appendChild(btn);
        document.body.appendChild(container);

        const msgs = container.querySelector('#botfy-messages');
        const input = container.querySelector('#botfy-input');
        const sendBtn = container.querySelector('#botfy-send');

        // Initial message
        addMessage('bot', `Olá! Sou ${agentName}. Como posso ajudar?`);

        // Toggle
        btn.addEventListener('click', () => {
            container.classList.toggle('open');
            if (container.classList.contains('open')) {
                btn.innerHTML = '✕';
                input.focus();
            } else {
                btn.innerHTML = '💬';
            }
        });
        container.querySelector('#botfy-close-btn').addEventListener('click', () => {
            container.classList.remove('open');
            btn.innerHTML = '💬';
        });

        // Send
        function addMessage(role, text) {
            const div = document.createElement('div');
            div.className = `botfy-msg ${role}`;
            div.innerHTML = `<div class="botfy-bubble">${text.replace(/\n/g, '<br>')}</div>`;
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
        }

        function showTyping() {
            const el = document.createElement('div');
            el.className = 'botfy-msg bot';
            el.id = 'botfy-typing';
            el.innerHTML = '<div class="botfy-bubble botfy-typing"><div class="botfy-dot"></div><div class="botfy-dot"></div><div class="botfy-dot"></div></div>';
            msgs.appendChild(el);
            msgs.scrollTop = msgs.scrollHeight;
        }

        function hideTyping() {
            const el = document.getElementById('botfy-typing');
            if (el) el.remove();
        }

        async function sendMessage() {
            const text = (input.value || '').trim();
            if (!text) return;
            input.value = '';
            sendBtn.disabled = true;
            addMessage('user', text);
            showTyping();
            try {
                const res = await fetch(`${apiUrl}/widget/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ agent_id: agentId, tenant_id: tenantId, message: text, session_id: getOrCreateSession() }),
                });
                const data = await res.json();
                hideTyping();
                addMessage('bot', data.reply || 'Erro ao responder.');
            } catch {
                hideTyping();
                addMessage('bot', 'Erro de conexão. Tente novamente.');
            } finally {
                sendBtn.disabled = false;
                input.focus();
            }
        }

        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
    }

    window.BotfyWidget = {
        init: function (config) {
            const apiUrl = (config.apiUrl || DEFAULT_API).replace(/\/$/, '');
            const color = config.color || '#2563EB';
            const position = config.position || 'right';
            const agentId = config.agentId;
            const tenantId = config.tenantId;
            if (!agentId || !tenantId) { console.warn('BotfyWidget: agentId e tenantId são obrigatórios.'); return; }

            // Fetch agent name from config endpoint
            fetch(`${apiUrl}/widget/config/${agentId}?tenant_id=${tenantId}`)
                .then(r => r.json())
                .then(data => {
                    buildWidget({ agentId, tenantId, apiUrl, agentName: data.name || 'Assistente', agentNiche: data.niche, color, position });
                })
                .catch(() => {
                    buildWidget({ agentId, tenantId, apiUrl, agentName: 'Assistente', agentNiche: '', color, position });
                });
        }
    };

    // Auto-init from script tag data attributes
    (function autoInit() {
        const script = document.currentScript || document.querySelector('script[data-agent-id]');
        if (!script) return;
        const agentId = script.getAttribute('data-agent-id');
        const tenantId = script.getAttribute('data-tenant-id');
        if (!agentId || !tenantId) return;
        window.BotfyWidget.init({
            agentId,
            tenantId,
            apiUrl: script.getAttribute('data-api-url') || DEFAULT_API,
            color: script.getAttribute('data-color') || '#2563EB',
            position: script.getAttribute('data-position') || 'right',
        });
    })();
})();
