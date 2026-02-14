"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type Agent = { id: string; name: string; niche: string | null; prompt_custom: string | null; active: boolean };

export default function AgentsPage() {
  const [list, setList] = useState<Agent[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<Agent[]>("/agents")
      .then(setList)
      .catch((e) => setErr(e.message));
  }, []);

  if (err) return <p className="text-red-600">{err}</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Meus agentes</h1>
        <Link
          href="/dashboard/agents/new"
          className="rounded-lg bg-blue-600 text-white px-4 py-2 hover:bg-blue-700"
        >
          Novo agente
        </Link>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
        <table className="w-full">
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
  );
}
