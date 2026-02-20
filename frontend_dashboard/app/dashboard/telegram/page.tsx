"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, getApiBase } from "@/lib/api";

type Tenant = { id: string; company_name: string };
type BotInfo = { bot_username: string | null; connected: boolean; agent_id?: string | null };
type Agent = { id: string; name: string; niche: string | null; prompt_custom: string | null; active: boolean };

function getErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "message" in err) {
    return String((err as { message: string }).message);
  }
  return "Não foi possível conectar. Verifique o token.";
}

export default function TelegramPage() {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [botInfo, setBotInfo] = useState<BotInfo | null>(null);
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [serverTokenCheck, setServerTokenCheck] = useState<{ valid: boolean; username?: string; error?: string } | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const load = () => {
    api<Tenant>("/tenants/me").then(setTenant).catch(() => setTenant(null));
    api<BotInfo>("/telegram/status")
      .then((data) => setBotInfo(data))
      .catch(() => setBotInfo(null));
    api<Agent[]>("/agents").then(setAgents).catch(() => setAgents([]));
  };

  useEffect(() => {
    load();
  }, []);

  const connectWithPayload = async (payload: { bot_token?: string; bot_token_b64?: string; use_server_token?: boolean }) => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await api("/telegram/connect", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setSuccess("Telegram conectado. Seu bot já pode receber mensagens.");
      setToken("");
      if (inputRef.current) inputRef.current.value = "";
      load();
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleConnectWithServerToken = async () => {
    await connectWithPayload({ use_server_token: true });
  };

  const handleCheckServerToken = async () => {
    setServerTokenCheck(null);
    setError(null);
    try {
      const res = await api<{ valid: boolean; username?: string; error?: string }>("/telegram/check-server-token");
      setServerTokenCheck(res);
    } catch {
      setServerTokenCheck({ valid: false, error: "Não foi possível contactar o servidor." });
    }
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    const raw = inputRef.current?.value ?? token;
    const t = String(raw ?? "").trim().replace(/\s/g, "");
    if (!t) {
      setError("Cole o token do bot do BotFather.");
      return;
    }
    if (t.length < 40 || t.length > 70) {
      setError("O token costuma ter 45–60 caracteres. Verifique se colou completo (sem espaços ou quebras).");
      return;
    }
    // Enviar em base64 evita corrupção por encoding no JSON (caracteres especiais, etc.)
    try {
      const b64 = typeof btoa !== "undefined" ? btoa(t) : Buffer.from(t, "utf-8").toString("base64");
      await connectWithPayload({ bot_token_b64: b64 });
    } catch {
      await connectWithPayload({ bot_token: t });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setSuccess(null);
    const reader = new FileReader();
    reader.onload = async () => {
      const t = String(reader.result ?? "").trim().replace(/\s/g, "");
      if (!t || t.length < 40) {
        setError("O arquivo deve conter apenas o token (uma linha, 45–60 caracteres).");
        return;
      }
      setLoading(true);
      try {
        const b64 = typeof btoa !== "undefined" ? btoa(t) : Buffer.from(t, "utf-8").toString("base64");
        await connectWithPayload({ bot_token_b64: b64 });
      } catch (err: unknown) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    reader.readAsText(file, "UTF-8");
    e.target.value = "";
  };

  const handleDisconnect = async () => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await api("/telegram/disconnect", { method: "DELETE" });
      setSuccess("Telegram desconectado.");
      load();
    } catch {
      setError("Não foi possível desconectar.");
    } finally {
      setLoading(false);
    }
  };

  const tenantId = tenant?.id ?? "";
  const botUsername = botInfo?.bot_username ?? "";
  const connected = botInfo?.connected ?? false;
  const telegramAgentId = botInfo?.agent_id ?? null;

  const handleSetTelegramAgent = async (agentId: string) => {
    const value = agentId === "" ? null : agentId;
    setError(null);
    try {
      await api("/telegram/agent", {
        method: "PATCH",
        body: JSON.stringify({ agent_id: value }),
      });
      load();
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    }
  };

  const deepLink =
    tenantId && botUsername
      ? `https://t.me/${botUsername}?start=t_${tenantId}`
      : "";

  const hasActiveAgent = agents.some((a) => a.active);

  return (
    <div className="space-y-4 sm:space-y-6">
      <h1 className="text-xl sm:text-2xl font-bold text-slate-800">Conexão Telegram</h1>

      <div className="max-w-xl space-y-6">
        {agents.length === 0 && (
          <div className="rounded-lg border-2 border-amber-200 bg-amber-50 p-4 sm:p-6">
            <h2 className="font-semibold text-amber-900 mb-2">Antes de conectar o Telegram</h2>
            <p className="text-amber-800 text-sm mb-3">
              O bot do Telegram usa um <strong>agente</strong> que você cria e treina no dashboard. Siga os passos:
            </p>
            <ol className="list-decimal list-inside text-amber-800 text-sm space-y-2 mb-4">
              <li>
                <Link href="/dashboard/agents/new" className="text-blue-600 hover:underline font-medium">
                  Crie um agente
                </Link>{" "}
                em <Link href="/dashboard/agents" className="text-blue-600 hover:underline">Meus agentes</Link>.
              </li>
              <li>
                <strong>Treine o agente:</strong> preencha nome, nicho e prompt customizado (instruções de como o bot deve responder).
              </li>
              <li>Deixe o agente <strong>Ativo</strong> (edite e marque como ativo se precisar).</li>
              <li>Volte aqui e conecte o Telegram com o token do BotFather.</li>
            </ol>
            <Link
              href="/dashboard/agents/new"
              className="inline-block rounded-lg bg-amber-600 text-white px-4 py-3 min-h-[44px] text-sm font-medium hover:bg-amber-700 flex items-center justify-center"
            >
              Criar meu primeiro agente
            </Link>
          </div>
        )}

        {agents.length > 0 && !hasActiveAgent && (
          <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-4 text-sm text-amber-800">
            Você tem agente(s), mas nenhum está <strong>Ativo</strong>. O Telegram só responde com um agente ativo.{" "}
            <Link href="/dashboard/agents" className="text-blue-600 hover:underline">Editar em Meus agentes</Link>.
          </div>
        )}

        <div className="rounded-lg border border-slate-200 bg-white p-4 sm:p-6">
          <h2 className="font-semibold text-slate-800 mb-2">Webhook (opcional)</h2>
          <p className="text-slate-600 text-sm mb-3">
            Use esta seção para o bot receber mensagens via URL pública (servidor, Vercel). Conecte com o token do servidor ou cole o token abaixo.
          </p>
          {connected ? (
            <div className="space-y-3">
              <p className="text-slate-600 text-sm">
                Conectado como <strong>@{botUsername}</strong>. O bot está ativo e recebendo mensagens.
              </p>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleDisconnect}
                  disabled={loading}
                  className="px-4 py-3 min-h-[44px] rounded-lg border border-red-200 text-red-700 hover:bg-red-50 disabled:opacity-50"
                >
                  Desconectar
                </button>
              </div>
              {agents.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-200">
                  <label className="block text-sm font-medium text-slate-700 mb-2">Agente deste bot (Telegram)</label>
                  <select
                    value={telegramAgentId ?? ""}
                    onChange={(e) => handleSetTelegramAgent(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 min-h-[44px] text-sm bg-white"
                  >
                    <option value="">Primeiro agente ativo</option>
                    {agents.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name} {a.niche ? `(${a.niche})` : ""} {!a.active ? "— inativo" : ""}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-slate-500 mt-1">Escolha qual agente responde neste Telegram. Pode ser diferente do WhatsApp.</p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-slate-600 text-sm mb-2">
                  Se o token está no <code className="bg-slate-100 px-1 rounded">.env</code> do servidor (<code className="bg-slate-100 px-1 rounded">TELEGRAM_BOT_TOKEN</code>):
                </p>
                <div className="flex flex-col sm:flex-row flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={handleCheckServerToken}
                    disabled={loading}
                    className="px-3 py-2.5 min-h-[44px] rounded-lg border border-slate-300 bg-white text-slate-700 text-sm hover:bg-slate-50"
                  >
                    Testar token do servidor
                  </button>
                  <button
                    type="button"
                    onClick={handleConnectWithServerToken}
                    disabled={loading}
                    className="px-4 py-3 min-h-[44px] rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 font-medium"
                  >
                    {loading ? "Conectando…" : "Conectar com token do servidor"}
                  </button>
                </div>
                {serverTokenCheck && (
                  <div className={`text-sm mt-2 ${serverTokenCheck.valid ? "text-green-700" : "text-red-600"}`}>
                    <p>
                      {serverTokenCheck.valid
                        ? `Token do servidor: válido (@${serverTokenCheck.username}). Pode clicar em Conectar.`
                        : `Token do servidor: ${serverTokenCheck.error}`}
                    </p>
                    {!serverTokenCheck.valid && serverTokenCheck.error?.includes("contactar o servidor") && (
                      <p className="text-slate-600 text-xs mt-2">
                        O dashboard não está alcançando o backend. URL chamada: <code className="bg-slate-100 px-1 rounded break-all">{getApiBase()}/telegram/check-server-token</code>. Confira: (1) Backend rodando? Na pasta do projeto: <code className="bg-slate-100 px-1 rounded">python run_platform_backend.py</code>. (2) Abra <a href="http://127.0.0.1:8000/health" target="_blank" rel="noopener noreferrer" className="underline">http://127.0.0.1:8000/health</a> no navegador — deve mostrar {`{"status":"ok"}`}.
                      </p>
                    )}
                  </div>
                )}
              </div>
              <div className="border-t border-slate-200 pt-3">
                <p className="text-slate-600 text-sm mb-2">Ou envie um arquivo .txt com apenas o token (evita colar):</p>
                <label className="inline-flex items-center gap-2 px-3 py-2.5 min-h-[44px] rounded-lg border border-slate-300 bg-white text-sm cursor-pointer hover:bg-slate-50">
                  <input type="file" accept=".txt,text/plain" onChange={handleFileSelect} disabled={loading} className="sr-only" />
                  <span>Selecionar arquivo .txt</span>
                </label>
              </div>
              <p className="text-slate-500 text-sm border-t border-slate-200 pt-3">Ou cole o token abaixo:</p>
            <form onSubmit={handleConnect} className="space-y-3">
              <div className="relative">
                <input
                  ref={inputRef}
                  type={showToken ? "text" : "password"}
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Ex: 7810006820:AAH..."
                  className="w-full rounded-lg border border-slate-300 pl-3 pr-10 py-2.5 min-h-[44px] text-sm font-mono"
                  autoComplete="off"
                  spellCheck={false}
                />
                <button
                  type="button"
                  onClick={() => setShowToken((s) => !s)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-500 hover:text-slate-700 rounded"
                  title={showToken ? "Ocultar token" : "Mostrar token"}
                  aria-label={showToken ? "Ocultar token" : "Mostrar token"}
                >
                  {showToken ? (
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-500">45–60 caracteres</p>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-3 min-h-[44px] rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 w-full sm:w-auto"
              >
                {loading ? "Conectando…" : "Conectar"}
              </button>
            </form>
            </div>
          )}
          {error && (
            <div className="mt-2">
              <p className="text-sm text-red-600">{error}</p>
              {error.toLowerCase().includes("token inválido") && (
                <p className="text-xs text-slate-600 mt-1">
                  Dica: confira no BotFather se não trocou o número <strong>1</strong> pela letra <strong>l</strong> (ou o contrário). Use o ícone do olho para conferir o token.
                </p>
              )}
              {error.includes("administrador") && (
                <p className="text-xs text-slate-500 mt-1">
                  Para administradores: defina <code className="bg-slate-100 px-1 rounded">TELEGRAM_WEBHOOK_BASE_URL</code> (ou <code className="bg-slate-100 px-1 rounded">WHATSAPP_WEBHOOK_BASE_URL</code>) no servidor com a URL pública do backend (ex.: https://seu-dominio.com). Em teste local use ngrok.
                </p>
              )}
            </div>
          )}
          {success && <p className="text-sm text-green-600 mt-2">{success}</p>}
        </div>

        {/* Link do tenant */}
        {tenantId && (
          <div className="rounded-lg border border-slate-200 bg-white p-4 sm:p-6">
            <h2 className="font-semibold text-slate-800 mb-2">Link do seu bot (compartilhe com clientes)</h2>
            {deepLink ? (
              <>
                <p className="text-sm text-slate-600 break-all font-mono bg-slate-50 border border-slate-200 rounded px-3 py-2">
                  {deepLink}
                </p>
                <p className="text-xs text-slate-500 mt-2">
                  Quem abrir esse link no Telegram já será associado à sua empresa.
                </p>
              </>
            ) : (
              <p className="text-sm text-slate-600">
                Conecte o bot acima para gerar o link exclusivo do seu tenant.
              </p>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
