"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { isAuthenticated, clearToken } from "@/lib/api";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/agents", label: "Meus agentes" },
  { href: "/dashboard/documents", label: "Base de conhecimento" },
  { href: "/dashboard/whatsapp", label: "WhatsApp" },
  { href: "/dashboard/telegram", label: "Telegram" },
  { href: "/dashboard/metrics", label: "Métricas" },
  { href: "/dashboard/plan", label: "Plano" },
];

function MenuIcon({ open }: { open: boolean }) {
  return open ? (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ) : (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!isAuthenticated()) router.replace("/login");
  }, [router]);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  function logout() {
    clearToken();
    setMenuOpen(false);
    router.replace("/login");
  }

  if (!mounted) return null;

  const NavContent = () => (
    <>
      <div className="p-4 border-b border-slate-700">
        <span className="font-semibold text-white">B&B RAG</span>
      </div>
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {nav.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={`block px-3 py-2.5 rounded-lg text-sm min-h-[44px] flex items-center ${
              pathname === href ? "bg-slate-600 text-white" : "text-slate-200 hover:bg-slate-700"
            }`}
          >
            {label}
          </Link>
        ))}
      </nav>
      <div className="p-2 border-t border-slate-700">
        <button
          type="button"
          onClick={logout}
          className="w-full text-left px-3 py-2.5 rounded-lg text-sm text-slate-300 hover:bg-slate-700 min-h-[44px] flex items-center"
        >
          Sair
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-slate-50">
      {/* Mobile header */}
      <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-slate-800 text-white shrink-0">
        <span className="font-semibold">B&B RAG</span>
        <button
          type="button"
          onClick={() => setMenuOpen((o) => !o)}
          className="p-2 -mr-2 rounded-lg hover:bg-slate-700 min-w-[44px] min-h-[44px] flex items-center justify-center"
          aria-expanded={menuOpen}
          aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
        >
          <MenuIcon open={menuOpen} />
        </button>
      </header>

      {/* Mobile drawer overlay */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMenuOpen(false)}
          aria-hidden
        />
      )}

      {/* Sidebar: drawer on mobile, fixed on desktop */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50 w-72 max-w-[85vw] lg:w-56 lg:max-w-none bg-slate-800 text-white flex flex-col shrink-0
          transform transition-transform duration-200 ease-out
          ${menuOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        <div className="flex flex-col h-full">
          <NavContent />
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0 w-full max-w-full p-4 sm:p-6 overflow-x-hidden overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
