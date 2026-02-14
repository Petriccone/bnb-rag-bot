"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type Tenant = { id: string; company_name: string; plan: string };
type Metrics = { agents_count: number; conversations_count: number; leads_count: number; messages_this_month: number; plan: string };

export default function DashboardPage() {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    Promise.all([
      api<Tenant>("/tenants/me").catch(() => null),
      api<Metrics>("/metrics").catch(() => null),
    ]).then(([t, m]) => {
      setTenant(t || null);
      setMetrics(m || null);
    }).catch((e) => setErr(e.message));
  }, []);

  if (err) return <p className="text-red-600">{err}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Dashboard</h1>
      {tenant && (
        <div className="mb-6 p-4 rounded-lg bg-white border border-slate-200">
          <p className="text-slate-600">
            <span className="font-medium">{tenant.company_name}</span> — Plano {tenant.plan}
          </p>
        </div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card title="Agentes" value={metrics?.agents_count ?? "—"} href="/dashboard/agents" />
        <Card title="Conversas" value={metrics?.conversations_count ?? "—"} />
        <Card title="Leads" value={metrics?.leads_count ?? "—"} />
        <Card title="Mensagens (mês)" value={metrics?.messages_this_month ?? "—"} />
      </div>
      <div className="flex gap-4">
        <Link
          href="/dashboard/agents"
          className="rounded-lg bg-blue-600 text-white px-4 py-2 hover:bg-blue-700"
        >
          Meus agentes
        </Link>
        <Link
          href="/dashboard/documents"
          className="rounded-lg border border-slate-300 px-4 py-2 hover:bg-slate-50"
        >
          Base de conhecimento
        </Link>
      </div>
    </div>
  );
}

function Card({
  title,
  value,
  href,
}: {
  title: string;
  value: number | string;
  href?: string;
}) {
  const content = (
    <div className="p-4 rounded-lg bg-white border border-slate-200">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="text-2xl font-semibold text-slate-800">{value}</p>
    </div>
  );
  if (href) return <Link href={href}>{content}</Link>;
  return content;
}
