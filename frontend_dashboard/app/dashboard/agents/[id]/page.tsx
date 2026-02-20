"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

type Agent = { id: string; name: string; niche: string | null; prompt_custom: string | null; active: boolean; embedding_namespace?: string | null };

type ChatMessage = { role: "user" | "assistant"; text: string };

export default function EditAgentPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const id = params.id as string;
  const [name, setName] = useState("");
  const [niche, setNiche] = useState("");
  const [prompt_custom, setPromptCustom] = useState("");
  const [active, setActive] = useState(true);
  const [embedding_namespace, setEmbeddingNamespace] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const showTestChat = searchParams.get("test") === "1";

  useEffect(() => {
    api<Agent>(`/agents/${id}`)
      .then((a) => {
        setName(a.name);
        setNiche(a.niche || "");
        setPromptCustom(a.prompt_custom || "");
        setActive(a.active);
        setEmbeddingNamespace(a.embedding_namespace || "");
      })
      .catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api(`/agents/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name,
          niche: niche || null,
          prompt_custom: prompt_custom || null,
          active,
          embedding_namespace: embedding_namespace.trim() || null,
        }),
      });
      router.replace("/dashboard/agents");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setLoading(false);
    }
  }

  async function sendChatMessage() {
    const msg = chatInput.trim();
    if (!msg || chatLoading) return;
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", text: msg }]);
    setChatLoading(true);
    try {
      const res = await api<{ reply: string }>(
        `/agents/${id}/chat`,
        { method: "POST", body: JSON.stringify({ message: msg }) },
        60000
      );
      setChatMessages((prev) => [...prev, { role: "assistant", text: res.reply || "(sem resposta)" }]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Erro: " + (err instanceof Error ? err.message : "Falha ao enviar") },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  if (error && !name) return <p className="text-red-600">{error}</p>;

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4 flex-wrap">
        <Link href="/dashboard/agents" className="text-slate-500 hover:text-slate-700 min-h-[44px] flex items-center self-start">
          ← Voltar
        </Link>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800">Editar agente</h1>
        {!showTestChat && (
          <button
            type="button"
            onClick={() => router.push(`/dashboard/agents/${id}?test=1`)}
            className="rounded-lg bg-emerald-600 text-white px-4 py-2 min-h-[44px] hover:bg-emerald-700 font-medium"
          >
            Testar conversa
          </button>
        )}
      </div>

      {showTestChat && (
        <section className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Testar conversa</h2>
          <div className="border border-slate-200 rounded-lg min-h-[200px] max-h-[360px] overflow-y-auto flex flex-col p-3 bg-slate-50">
            {chatMessages.length === 0 && (
              <p className="text-slate-500 text-sm">Envie uma mensagem para testar o agente.</p>
            )}
            {chatMessages.map((m, i) => (
              <div
                key={i}
                className={`mb-2 max-w-[85%] ${m.role === "user" ? "self-end bg-blue-600 text-white" : "self-start bg-white border border-slate-200"} rounded-lg px-3 py-2 text-sm`}
              >
                {m.text}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <div className="flex gap-2 mt-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendChatMessage()}
              placeholder="Digite uma mensagem..."
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2.5 min-h-[44px]"
              disabled={chatLoading}
            />
            <button
              type="button"
              onClick={sendChatMessage}
              disabled={chatLoading || !chatInput.trim()}
              className="rounded-lg bg-emerald-600 text-white px-4 py-2.5 min-h-[44px] hover:bg-emerald-700 disabled:opacity-50 font-medium"
            >
              {chatLoading ? "..." : "Enviar"}
            </button>
          </div>
        </section>
      )}

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
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Base de conhecimento (namespace)</label>
          <input
            type="text"
            value={embedding_namespace}
            onChange={(e) => setEmbeddingNamespace(e.target.value)}
            placeholder="ex: agente_vendas (use o mesmo ao enviar documentos)"
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 min-h-[44px]"
          />
          <p className="text-xs text-slate-500 mt-1">
            Ao enviar documentos na Base de conhecimento, use este mesmo valor em &quot;Namespace&quot; para este agente.
          </p>
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
