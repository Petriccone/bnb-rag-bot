"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      const access_token = data?.access_token;
      if (!access_token) {
        setError("Resposta inválida do servidor. Tente novamente.");
        return;
      }
      setToken(access_token);
      router.replace("/dashboard");
    } catch (err: unknown) {
      if (typeof window !== "undefined") console.error("[Login] Erro:", err);
      const message = err instanceof Error ? err.message : "Erro ao entrar. Tente novamente.";
      setError(message || "Erro ao entrar. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white shadow-lg p-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Entrar</h1>
        <p className="text-slate-500 text-sm mb-6">Dashboard B&B RAG</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div role="alert" className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-red-700 text-sm">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 min-h-[44px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 min-h-[44px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 text-white py-3 min-h-[44px] font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Não tem conta?{" "}
          <Link href="/register" className="text-blue-600 hover:underline">
            Cadastre sua empresa
          </Link>
        </p>
      </div>
    </div>
  );
}
