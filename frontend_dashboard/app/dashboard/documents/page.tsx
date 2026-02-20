"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Doc = {
  id: string;
  file_path: string;
  file_name?: string;
  file_size_mb?: number;
  file_type?: string;
  embedding_namespace: string;
  source_url?: string | null;
  status?: string;
};

/** URL do POST /api/documents/upload: mesma origem (rewrite encaminha para o backend). */
function getDocumentsUploadUrl(): string {
  if (typeof window !== "undefined" && window.location?.origin) {
    const o = String(window.location.origin).replace(/\/+$/, "");
    const api = o.endsWith("/api") ? o : `${o}/api`;
    return `${api}/documents/upload`;
  }
  const fallback = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || "http://127.0.0.1:8000";
  const base = String(fallback).replace(/\/+$/, "");
  const api = base.endsWith("/api") ? base : `${base}/api`;
  return `${api}/documents/upload`;
}

export default function DocumentsPage() {
  const [list, setList] = useState<Doc[]>([]);
  const [err, setErr] = useState("");
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  function load() {
    api<Doc[]>("/documents")
      .then(setList)
      .catch((e) => setErr(e.message));
  }

  useEffect(() => load(), []);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setErr("");
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const url = getDocumentsUploadUrl();
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);
      const res = await fetch(url, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/bda2a585-6330-4387-9d59-18331d5ab5ec',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'21fe81'},body:JSON.stringify({sessionId:'21fe81',location:'documents/page.tsx:upload',message:'upload !res.ok',data:{status:res.status,statusText:res.statusText,body},hypothesisId:'D',timestamp:Date.now()})}).catch(()=>{});
        // #endregion
        const detail = typeof body.detail === "string" ? body.detail : body.detail?.message ?? "Erro no servidor";
        throw new Error(detail);
      }
      setFile(null);
      load();
    } catch (e) {
      if (e instanceof Error) {
        if (e.name === "AbortError") setErr("Upload demorou muito (timeout). Tente um arquivo menor.");
        else if (e.message === "Failed to fetch" || e.message.includes("fetch"))
          setErr("Não foi possível conectar à API. No projeto do dashboard (Vercel), defina BACKEND_URL com a URL da API (ex.: https://bnb-rag-api.vercel.app) e faça redeploy.");
        else setErr(e.message);
      } else setErr("Erro no upload");
    } finally {
      setUploading(false);
    }
  }

  async function remove(id: string) {
    if (!confirm("Remover este documento?")) return;
    try {
      await api(`/documents/${id}`, { method: "DELETE" });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao remover");
    }
  }

  const displayName = (d: Doc) => d.file_name ?? d.file_path;

  return (
    <div className="space-y-4 sm:space-y-6">
      <h1 className="text-xl sm:text-2xl font-bold text-slate-800">Base de conhecimento</h1>
      <p className="text-slate-600 text-sm sm:text-base">
        Envie documentos para alimentar a base de conhecimento. O bot (Telegram/WhatsApp) usa esse conteúdo para responder com contexto. Formatos: PDF, TXT, Excel (.xlsx, .xls), Word (.docx), CSV, Markdown (.md), HTML.
      </p>

      <form onSubmit={handleUpload} className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-end gap-3 sm:gap-4 mb-6 sm:mb-8">
        <div className="flex-1 min-w-0">
          <label className="block text-sm font-medium text-slate-700 mb-1">Arquivo</label>
          <input
            type="file"
            accept=".pdf,.txt,.xlsx,.xls,.docx,.csv,.md,.html"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-slate-500 file:mr-2 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 min-h-[44px]"
          />
        </div>
        <button
          type="submit"
          disabled={!file || uploading}
          className="rounded-lg bg-blue-600 text-white px-4 py-3 sm:py-2 hover:bg-blue-700 disabled:opacity-50 min-h-[44px] font-medium"
        >
          {uploading ? "Enviando..." : "Enviar"}
        </button>
      </form>

      {err && <p className="text-red-600 text-sm">{err}</p>}

      {/* Mobile: lista em cards */}
      <div className="md:hidden space-y-3">
        {list.length === 0 && (
          <div className="p-6 rounded-lg border border-slate-200 bg-white text-center text-slate-500">
            Nenhum documento. Envie o primeiro.
          </div>
        )}
        {list.map((d) => (
          <div
            key={d.id}
            className="p-4 rounded-lg border border-slate-200 bg-white flex flex-col gap-2"
          >
            <p className="font-medium text-slate-800 truncate" title={displayName(d)}>
              {displayName(d)}
            </p>
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-slate-600">
              <span>Tipo: {d.file_type ?? "—"}</span>
              <span>Status: {d.status ?? "—"}</span>
            </div>
            <button
              type="button"
              onClick={() => remove(d.id)}
              className="self-start mt-1 text-red-600 hover:underline text-sm min-h-[44px] flex items-center"
            >
              Remover
            </button>
          </div>
        ))}
      </div>

      {/* Desktop: tabela */}
      <div className="hidden md:block rounded-lg border border-slate-200 bg-white overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-slate-600">Arquivo</th>
                <th className="text-left p-3 text-sm font-medium text-slate-600">Tipo</th>
                <th className="text-left p-3 text-sm font-medium text-slate-600">Status</th>
                <th className="text-left p-3 text-sm font-medium text-slate-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {list.length === 0 && (
                <tr>
                  <td colSpan={4} className="p-6 text-center text-slate-500">
                    Nenhum documento. Envie o primeiro.
                  </td>
                </tr>
              )}
              {list.map((d) => (
                <tr key={d.id} className="border-b border-slate-100">
                  <td className="p-3 font-medium truncate max-w-xs">{displayName(d)}</td>
                  <td className="p-3 text-slate-600">{d.file_type ?? "—"}</td>
                  <td className="p-3 text-slate-600">{d.status ?? "—"}</td>
                  <td className="p-3">
                    <button
                      type="button"
                      onClick={() => remove(d.id)}
                      className="text-red-600 hover:underline text-sm"
                    >
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
