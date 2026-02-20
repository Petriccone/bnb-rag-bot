"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type Agent = { id: string; name: string; niche: string | null; prompt_custom: string | null; active: boolean };

export default function AgentsPage() {
  const [list, setList] = useState<Agent[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setErr("");
    api<unknown>("/agents")
      .then((data) => {
        const arr = Array.isArray(data) ? data : [];
        setList(arr as Agent[]);
      })
      .catch((e) => {
        setErr(e instanceof Error ? e.message : "Erro ao carregar agentes.");
        setList([]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-slate-500">Carregando agentes...</p>;
  if (err) return <p className="text-red-600">{err}</p>;

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center">
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800">Meus agentes</h1>
        <Link
          href="/dashboard/agents/new"
          className="rounded-lg bg-blue-600 text-white px-4 py-3 sm:py-2 hover:bg-blue-700 text-center font-medium min-h-[44px] flex items-center justify-center sm:inline-flex"
        >
          Novo agente
        </Link>
      </div>

      {/* Mobile: cards */}
      <div className="md:hidden space-y-3">
        {list.length === 0 && (
          <div className="p-6 rounded-lg border border-slate-200 bg-white text-center text-slate-500">
            Nenhum agente. Crie o primeiro.
          </div>
        )}
        {list.map((a) => (
          <div
            key={a.id}
            className="p-4 rounded-lg border border-slate-200 bg-white flex flex-col gap-2"
          >
            <p className="font-medium text-slate-800">{a.name}</p>
            <p className="text-sm text-slate-600">{a.niche || "—"}</p>
            <span className={a.active ? "text-green-600 text-sm" : "text-slate-400 text-sm"}>
              {a.active ? "Ativo" : "Inativo"}
            </span>
            <Link
              href={`/dashboard/agents/${a.id}`}
              className="self-start mt-1 text-blue-600 hover:underline text-sm min-h-[44px] flex items-center"
            >
              Editar
            </Link>
          </div>
        ))}
      </div>

      {/* Desktop: tabela */}
      <div className="hidden md:block rounded-lg border border-slate-200 bg-white overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-slate-600">Nome</th>
                <th className="text-left p-3 text-sm font-medium text-slate-600">Nicho</th>
                <th className="text-left p-3 text-sm font-medium text-slate-600">Status</th>
                <th className="text-left p-3 text-sm font-medium text-slate-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {list.length === 0 && (
                <tr>
                  <td colSpan={4} className="p-6 text-center text-slate-500">
                    Nenhum agente. Crie o primeiro.
                  </td>
                </tr>
              )}
              {list.map((a) => (
                <tr key={a.id} className="border-b border-slate-100">
                  <td className="p-3 font-medium">{a.name}</td>
                  <td className="p-3 text-slate-600">{a.niche || "—"}</td>
                  <td className="p-3">
                    <span className={a.active ? "text-green-600" : "text-slate-400"}>
                      {a.active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td className="p-3">
                    <Link
                      href={`/dashboard/agents/${a.id}`}
                      className="text-blue-600 hover:underline text-sm"
                    >
                      Editar
                    </Link>
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
