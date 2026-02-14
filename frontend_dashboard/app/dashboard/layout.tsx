"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { isAuthenticated, clearToken, api } from "@/lib/api";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/agents", label: "Meus agentes" },
  { href: "/dashboard/documents", label: "Base de conhecimento" },
  { href: "/dashboard/whatsapp", label: "WhatsApp" },
  { href: "/dashboard/telegram", label: "Telegram" },
  { href: "/dashboard/metrics", label: "Métricas" },
  { href: "/dashboard/plan", label: "Plano" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!isAuthenticated()) router.replace("/login");
  }, [router]);

  function logout() {
    clearToken();
    router.replace("/login");
  }

  if (!mounted) return null;

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-slate-800 text-white flex flex-col">
        <div className="p-4 border-b border-slate-700">
          <span className="font-semibold">B&B RAG</span>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {nav.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`block px-3 py-2 rounded-lg text-sm ${
                pathname === href ? "bg-slate-600" : "hover:bg-slate-700"
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
        <div className="p-2 border-t border-slate-700">
          <button
            onClick={logout}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-700"
          >
            Sair
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  );
}
