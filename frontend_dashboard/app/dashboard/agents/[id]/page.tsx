"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

type Agent = { id: string; name: string; niche: string | null; prompt_custom: string | null; active: boolean };

export default function EditAgentPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const [name, setName] = useState("");
  const [niche, setNiche] = useState("");
  const [prompt_custom, setPromptCustom] = useState("");
  const [active, setActive] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api<Agent>(`/agents/${id}`)
      .then((a) => {
        setName(a.name);
        setNiche(a.niche || "");
        setPromptCustom(a.prompt_custom || "");
        setActive(a.active);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api(`/agents/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ name, niche: niche || null, prompt_custom: prompt_custom || null, active }),
      });
      router.replace("/dashboard/agents");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setLoading(false);
    }
  }

  if (error && !name) return <p className="text-red-600">{error}</p>;

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
        <Link href="/dashboard/agents" className="text-slate-500 hover:text-slate-700 min-h-[44px] flex items-center self-start">
          ← Voltar
        </Link>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800">Editar agente</h1>
      </div>
      <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Nome</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 min-h-[44px]"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Nicho</label>
          <input
            type="text"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 min-h-[44px]"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Prompt customizado</label>
          <textarea
            value={prompt_custom}
            onChange={(e) => setPromptCustom(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 min-h-[100px]"
          />
        </div>
        <div className="flex items-center gap-3 min-h-[44px]">
          <input
            type="checkbox"
            id="active"
            checked={active}
            onChange={(e) => setActive(e.target.checked)}
            className="rounded border-slate-300 w-5 h-5"
          />
          <label htmlFor="active" className="text-sm text-slate-700">Agente ativo</label>
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-blue-600 text-white px-4 py-3 min-h-[44px] hover:bg-blue-700 disabled:opacity-50 font-medium"
        >
          {loading ? "Salvando..." : "Salvar"}
        </button>
      </form>
    </div>
  );
}
