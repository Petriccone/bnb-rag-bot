"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Metrics = {
  agents_count: number;
  conversations_count: number;
  leads_count: number;
  messages_this_month: number;
  plan: string;
};

export default function MetricsPage() {
  const [m, setM] = useState<Metrics | null>(null);

  useEffect(() => {
    api<Metrics>("/metrics").then(setM).catch(() => setM(null));
  }, []);

  if (!m) return <p className="text-slate-500">Carregando métricas...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Métricas</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-6 rounded-lg bg-white border border-slate-200">
          <p className="text-sm text-slate-500">Plano</p>
          <p className="text-xl font-semibold text-slate-800 capitalize">{m.plan}</p>
        </div>
        <div className="p-6 rounded-lg bg-white border border-slate-200">
          <p className="text-sm text-slate-500">Agentes</p>
          <p className="text-xl font-semibold text-slate-800">{m.agents_count}</p>
        </div>
        <div className="p-6 rounded-lg bg-white border border-slate-200">
          <p className="text-sm text-slate-500">Conversas</p>
          <p className="text-xl font-semibold text-slate-800">{m.conversations_count}</p>
        </div>
        <div className="p-6 rounded-lg bg-white border border-slate-200">
          <p className="text-sm text-slate-500">Leads</p>
          <p className="text-xl font-semibold text-slate-800">{m.leads_count}</p>
        </div>
        <div className="p-6 rounded-lg bg-white border border-slate-200 sm:col-span-2">
          <p className="text-sm text-slate-500">Mensagens neste mês</p>
          <p className="text-xl font-semibold text-slate-800">{m.messages_this_month}</p>
        </div>
      </div>
      <div className="mt-6 p-4 rounded-lg bg-slate-50 border border-slate-200 text-sm text-slate-600">
        <p>Free: 1 agente, 500 msgs/mês. Pro: 5 agentes, 10k msgs/mês. Enterprise: ilimitado.</p>
      </div>
    </div>
  );
}
