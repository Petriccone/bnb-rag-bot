"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Doc = { id: string; file_path: string; embedding_namespace: string };

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
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
    try {
      const res = await fetch(`${base}/documents`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
      if (!res.ok) throw new Error(await res.json().then((x: { detail?: string }) => x.detail).catch(() => "Erro"));
      setFile(null);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro no upload");
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
        Envie documentos para o RAG do seu tenant. O namespace é isolado por tenant.
      </p>

      <form onSubmit={handleUpload} className="flex flex-wrap items-end gap-4 mb-8">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Arquivo</label>
          <input
            type="file"
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
