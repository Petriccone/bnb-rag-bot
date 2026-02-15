"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

export default function NewAgentPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [niche, setNiche] = useState("");
  const [prompt_custom, setPromptCustom] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api("/agents", {
        method: "POST",
        body: JSON.stringify({ name, niche: niche || null, prompt_custom: prompt_custom || null }),
      });
      router.replace("/dashboard/agents");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar agente");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center gap-4">
        <Link href="/dashboard/agents" className="text-slate-500 hover:text-slate-700">
          ← Voltar
        </Link>
        <h1 className="text-2xl font-bold text-slate-800">Novo agente</h1>
      </div>
      <p className="text-slate-600 text-sm mb-6 max-w-xl">
        Este agente pode ser usado no bot do Telegram. <strong>Treinar</strong> o agente é preencher nome, nicho e o prompt customizado (instruções de como o bot deve responder). Depois de criar, ative o agente e conecte o Telegram na página Conexão Telegram.
      </p>
      <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Nome</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Nicho</label>
          <input
            type="text"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            placeholder="ex.: imóveis, filtros"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Prompt customizado (opcional)</label>
          <textarea
            value={prompt_custom}
            onChange={(e) => setPromptCustom(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 min-h-[100px]"
            placeholder="Instruções adicionais ao agente SDR (SPIN é sempre aplicado)"
          />
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-blue-600 text-white px-4 py-2 hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Criando..." : "Criar agente"}
        </button>
      </form>
    </div>
  );
}
