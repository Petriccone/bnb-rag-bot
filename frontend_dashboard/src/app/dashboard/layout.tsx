"use client";

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useI18n } from '@/lib/i18n-context';
import LanguageSelector from '@/components/LanguageSelector';
import { ThemeToggle } from '@/components/ThemeToggle';
import Link from 'next/link';
import {
    CreditCard,
    LayoutDashboard,
    Settings,
    Users,
    LogOut,
    Bot,
    BookOpen,
    Smartphone
} from 'lucide-react';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const { t } = useI18n();
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
        const token = localStorage.getItem('access_token');
        if (!token && !pathname.includes('/login') && !pathname.includes('/register')) {
            router.push('/login');
        }
    }, [pathname, router]);

    if (!isMounted) return null;

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('tenant_id');
        router.push('/login');
    };

    const navItems = [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Agentes', href: '/dashboard/agents', icon: Bot },
        { name: 'Treinamento', href: '/dashboard/training', icon: BookOpen },
        { name: 'Equipe', href: '/dashboard/team', icon: Users },
        { name: 'Planos', href: '/dashboard/billing', icon: CreditCard },
        { name: 'Integrações', href: '/dashboard/integrations', icon: Smartphone },
        { name: 'Configurações', href: '/dashboard/settings', icon: Settings },
    ];

    return (
        <div className="flex h-screen bg-gray-50 dark:bg-[#0b0e14] transition-colors duration-200">
            {/* Sidebar */}
            <div className="w-64 bg-white dark:bg-[#111827] border-r border-gray-200 dark:border-[#1f2937] flex flex-col transition-colors duration-200">
                <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-[#1f2937]">
                    <span className="text-xl font-extrabold tracking-tight">
                        <span className="text-gray-900 dark:text-gray-100">Bot</span><span className="text-[#8b5cf6]">fy</span>
                    </span>
                </div>

                <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg group transition ${isActive
                                    ? 'bg-blue-50 dark:bg-[#1f2937] text-blue-700 dark:text-white'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-[#1f2937] hover:text-gray-900 dark:hover:text-white'
                                    }`}
                            >
                                <item.icon
                                    className={`mr-3 flex-shrink-0 h-5 w-5 ${isActive ? 'text-[#8b5cf6]' : 'text-gray-500 group-hover:text-gray-300'
                                        }`}
                                    aria-hidden="true"
                                />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-gray-200 dark:border-[#1f2937] transition-colors duration-200">
                    <button
                        onClick={handleLogout}
                        className="flex w-full items-center px-3 py-2 text-sm font-medium text-red-600 dark:text-red-500 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition"
                    >
                        <LogOut className="mr-3 flex-shrink-0 h-5 w-5 text-red-500" />
                        {t.signOut}
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Top bar with language selector */}
                <header className="h-14 bg-white dark:bg-[#111827] border-b border-gray-200 dark:border-[#1f2937] flex items-center justify-end px-6 transition-colors duration-200">
                    <ThemeToggle />
                    <LanguageSelector />
                </header>
                <main className="flex-1 overflow-y-auto p-8 bg-gray-50 dark:bg-[#0b0e14] text-gray-900 dark:text-gray-100 transition-colors duration-200">
                    {children}
                </main>
            </div>
        </div>
    );
}
