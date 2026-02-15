"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Doc = { id: string; file_path: string; embedding_namespace: string };

/** URL do POST /api/documents: evita barra dupla e garante /api no path. */
function getDocumentsUploadUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  const raw =
    (typeof envUrl === "string" ? envUrl.trim() : "") ||
    (typeof window !== "undefined" ? window.location.origin : "") ||
    "http://127.0.0.1:8000";
  const origin = String(raw).replace(/\/+$/, "");
  const apiBase = origin.endsWith("/api") ? origin : `${origin}/api`;
  return `${apiBase.replace(/\/+$/, "")}/documents`;
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
        const detail = typeof body.detail === "string" ? body.detail : body.detail?.message ?? "Erro no servidor";
        throw new Error(detail);
      }
      setFile(null);
      load();
    } catch (e) {
      if (e instanceof Error) {
        if (e.name === "AbortError") setErr("Upload demorou muito (timeout). Tente um arquivo menor.");
        else if (e.message === "Failed to fetch" || e.message.includes("fetch"))
          setErr("Não foi possível conectar à API. Verifique se o backend está rodando e se NEXT_PUBLIC_API_URL está correto no .env do dashboard.");
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

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Base de conhecimento</h1>
      <p className="text-slate-600 mb-6">
        Envie documentos ou imagens para alimentar a base de conhecimento. O bot (Telegram/WhatsApp) usa esse conteúdo para responder com contexto. Formatos aceitos: PDF, TXT, Excel (.xlsx, .xls), imagens (PNG, JPG). O processamento é automático após o upload.
      </p>

      <form onSubmit={handleUpload} className="flex flex-wrap items-end gap-4 mb-8">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Arquivo</label>
          <input
            type="file"
            accept=".pdf,.txt,.xlsx,.xls,.png,.jpg,.jpeg"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700"
          />
        </div>
        <button
          type="submit"
          disabled={!file || uploading}
          className="rounded-lg bg-blue-600 text-white px-4 py-2 hover:bg-blue-700 disabled:opacity-50"
        >
          {uploading ? "Enviando..." : "Enviar"}
        </button>
      </form>

      {err && <p className="text-red-600 text-sm mb-4">{err}</p>}

      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left p-3 text-sm font-medium text-slate-600">Arquivo</th>
              <th className="text-left p-3 text-sm font-medium text-slate-600">Namespace</th>
              <th className="text-left p-3 text-sm font-medium text-slate-600">Ações</th>
            </tr>
          </thead>
          <tbody>
            {list.length === 0 && (
              <tr>
                <td colSpan={3} className="p-6 text-center text-slate-500">
                  Nenhum documento. Envie o primeiro.
                </td>
              </tr>
            )}
            {list.map((d) => (
              <tr key={d.id} className="border-b border-slate-100">
                <td className="p-3 font-medium truncate max-w-xs">{d.file_path}</td>
                <td className="p-3 text-slate-600">{d.embedding_namespace}</td>
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
  );
}
