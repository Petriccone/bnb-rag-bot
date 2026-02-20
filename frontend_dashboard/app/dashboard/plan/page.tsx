"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Tenant = { id: string; company_name: string; plan: string; settings: Record<string, unknown> };

export default function PlanPage() {
  const [tenant, setTenant] = useState<Tenant | null>(null);

  useEffect(() => {
    api<Tenant>("/tenants/me").then(setTenant).catch(() => setTenant(null));
  }, []);

  if (!tenant) return <p className="text-slate-500">Carregando...</p>;

  return (
    <div className="space-y-4 sm:space-y-6">
      <h1 className="text-xl sm:text-2xl font-bold text-slate-800">Configuração de plano</h1>
      <div className="max-w-xl rounded-lg border border-slate-200 bg-white p-4 sm:p-6 space-y-4">
        <p>
          <span className="text-slate-500">Empresa:</span>{" "}
          <span className="font-medium">{tenant.company_name}</span>
        </p>
        <p>
          <span className="text-slate-500">Plano atual:</span>{" "}
          <span className="font-medium capitalize">{tenant.plan}</span>
        </p>
        <div className="pt-4 border-t border-slate-200 text-sm text-slate-600">
          <p className="font-medium mb-2">Limites por plano:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Free: 1 agente, 500 mensagens/mês</li>
            <li>Pro: 5 agentes, 10.000 mensagens/mês</li>
            <li>Enterprise: ilimitado</li>
          </ul>
          <p className="mt-4 text-slate-500">
            Alteração de plano é feita pela administração. Entre em contato para upgrade.
          </p>
        </div>
      </div>
    </div>
  );
}
