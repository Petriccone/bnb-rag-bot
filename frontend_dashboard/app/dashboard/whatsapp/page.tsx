"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Status = {
  connected: boolean;
  message: string;
  phone_number_id_mask?: string | null;
  connection_type?: string | null;
};

type EvolutionAvailable = { available: boolean };

type EvolutionQR = { instance_name: string; qr_code_base64?: string; pairing_code?: string };

export default function WhatsAppPage() {
  const [status, setStatus] = useState<Status | null>(null);
  const [evolutionAvailable, setEvolutionAvailable] = useState(false);
  const [qr, setQr] = useState<EvolutionQR | null>(null);
  const [phoneNumberId, setPhoneNumberId] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [evoBaseUrl, setEvoBaseUrl] = useState("");
  const [evoApiKey, setEvoApiKey] = useState("");
  const [evoInstance, setEvoInstance] = useState("");
  const [loadingQr, setLoadingQr] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [connectingEvo, setConnectingEvo] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState("");

  function loadStatus() {
    api<Status>("/whatsapp/status")
      .then(setStatus)
      .catch(() => setStatus({ connected: false, message: "Erro ao carregar status." }));
  }

  useEffect(() => {
    loadStatus();
    api<EvolutionAvailable>("/whatsapp/evolution-available").then((r) => setEvolutionAvailable(r.available)).catch(() => setEvolutionAvailable(false));
  }, []);

  async function handleRequestQr() {
    setError("");
    setLoadingQr(true);
    setQr(null);
    try {
      const data = await api<EvolutionQR>("/whatsapp/evolution-request-qr", { method: "POST" });
      setQr(data);
      loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar QR");
    } finally {
      setLoadingQr(false);
    }
  }

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setConnecting(true);
    try {
      await api("/whatsapp/connect", {
        method: "POST",
        body: JSON.stringify({ phone_number_id: phoneNumberId.trim(), access_token: accessToken.trim() }),
      });
      setPhoneNumberId("");
      setAccessToken("");
      loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao conectar");
    } finally {
      setConnecting(false);
    }
  }

  async function handleConnectEvolution(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setConnectingEvo(true);
    try {
      await api("/whatsapp/connect-evolution", {
        method: "POST",
        body: JSON.stringify({
          base_url: evoBaseUrl.trim(),
          api_key: evoApiKey.trim(),
          instance_name: evoInstance.trim(),
        }),
      });
      setEvoBaseUrl("");
      setEvoApiKey("");
      setEvoInstance("");
      loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao conectar Evolution");
    } finally {
      setConnectingEvo(false);
    }
  }

  async function handleDisconnect() {
    if (!confirm("Desconectar WhatsApp? O número deixará de receber respostas do agente.")) return;
    setDisconnecting(true);
    setError("");
    try {
      await api("/whatsapp/disconnect", { method: "DELETE" });
      loadStatus();
      setQr(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao desconectar");
    } finally {
      setDisconnecting(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Conexão WhatsApp</h1>

      <div className="max-w-xl rounded-lg border border-slate-200 bg-white p-6 mb-6">
        {status ? (
          <>
            <p className="text-slate-600 mb-2">{status.message}</p>
            <p>
              Status:{" "}
              <span className={status.connected ? "text-green-600 font-medium" : "text-amber-600"}>
                {status.connected ? "Conectado" : "Não conectado"}
              </span>
              {status.connection_type === "evolution" && (
                <span className="ml-2 text-slate-500 text-sm">(QR Code)</span>
              )}
              {status.phone_number_id_mask && (
                <span className="ml-2 text-slate-500 text-sm">({status.phone_number_id_mask})</span>
              )}
            </p>
            {status.connected && (
              <button
                type="button"
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="mt-4 rounded-lg border border-red-200 text-red-700 px-4 py-2 hover:bg-red-50 disabled:opacity-50"
              >
                {disconnecting ? "Desconectando..." : "Desconectar"}
              </button>
            )}
          </>
        ) : (
          <p className="text-slate-500">Carregando...</p>
        )}
      </div>

      {status && !status.connected && (
        <div className="space-y-6 max-w-xl">
          {/* Opção simples: só escanear QR (quando admin configurou Evolution) */}
          {evolutionAvailable && (
            <div className="rounded-lg border border-green-200 bg-green-50/50 p-6">
              <h2 className="font-semibold text-slate-800 mb-1">Conectar em 2 passos</h2>
              <p className="text-sm text-slate-600 mb-4">
                Clique no botão abaixo e escaneie o QR Code com o WhatsApp do celular (WhatsApp → Aparelhos conectados → Conectar aparelho). Nada para instalar.
              </p>
              {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
              <button
                type="button"
                onClick={handleRequestQr}
                disabled={loadingQr}
                className="rounded-lg bg-green-600 text-white px-4 py-2 hover:bg-green-700 disabled:opacity-50"
              >
                {loadingQr ? "Gerando QR..." : "Mostrar QR Code"}
              </button>
              {qr && (
                <div className="mt-4">
                  {qr.qr_code_base64 ? (
                    <img
                      src={typeof qr.qr_code_base64 === "string" && qr.qr_code_base64.startsWith("data:") ? qr.qr_code_base64 : `data:image/png;base64,${qr.qr_code_base64}`}
                      alt="QR Code WhatsApp"
                      className="border border-slate-200 rounded-lg max-w-[240px]"
                    />
                  ) : qr.pairing_code ? (
                    <p className="text-slate-700">Código de pareamento: <strong>{qr.pairing_code}</strong></p>
                  ) : null}
                  <p className="text-xs text-slate-500 mt-2">Abra o WhatsApp no celular e escaneie o QR ou use o código.</p>
                </div>
              )}
            </div>
          )}

          {/* Cloud API (Meta) - sempre visível */}
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-slate-800 mb-1">Ou: WhatsApp Cloud API (Meta)</h2>
            <p className="text-sm text-slate-600 mb-4">
              Se você tem conta Meta for Developers, use Phone Number ID e Access Token.
            </p>
            <form onSubmit={handleConnect} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number ID</label>
                <input
                  type="text"
                  value={phoneNumberId}
                  onChange={(e) => setPhoneNumberId(e.target.value)}
                  placeholder="Ex.: 123456789012345"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Access Token</label>
                <input
                  type="password"
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  placeholder="Token do Meta"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>
              {error && !evolutionAvailable && <p className="text-red-600 text-sm">{error}</p>}
              <button
                type="submit"
                disabled={connecting}
                className="rounded-lg border border-slate-300 px-4 py-2 hover:bg-slate-50 disabled:opacity-50"
              >
                {connecting ? "Conectando..." : "Conectar com Cloud API"}
              </button>
            </form>
          </div>

          {/* Evolution manual (só se não tiver QR disponível) - para quem tem própria Evolution */}
          {!evolutionAvailable && (
            <div className="rounded-lg border border-slate-200 bg-white p-6">
              <h2 className="font-semibold text-slate-800 mb-1">Ou: Evolution API (URL própria)</h2>
              <p className="text-sm text-slate-600 mb-4">
                Se você já tem uma Evolution API (sua ou de um provedor), informe a URL, API Key e nome da instância.
              </p>
              <form onSubmit={handleConnectEvolution} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">URL da Evolution API</label>
                  <input
                    type="url"
                    value={evoBaseUrl}
                    onChange={(e) => setEvoBaseUrl(e.target.value)}
                    placeholder="https://sua-evolution.com"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">API Key</label>
                  <input
                    type="password"
                    value={evoApiKey}
                    onChange={(e) => setEvoApiKey(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Nome da instância</label>
                  <input
                    type="text"
                    value={evoInstance}
                    onChange={(e) => setEvoInstance(e.target.value)}
                    placeholder="Ex.: minha-instancia"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </div>
                <button
                  type="submit"
                  disabled={connectingEvo}
                  className="rounded-lg border border-slate-300 px-4 py-2 hover:bg-slate-50 disabled:opacity-50"
                >
                  {connectingEvo ? "Conectando..." : "Conectar"}
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
