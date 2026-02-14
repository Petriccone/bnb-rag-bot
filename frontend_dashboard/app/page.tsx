"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    if (isAuthenticated()) router.replace("/dashboard");
    else router.replace("/login");
  }, [router]);
  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-slate-500">Redirecionando...</p>
    </div>
  );
}
