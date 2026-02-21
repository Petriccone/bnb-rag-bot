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
    Smartphone,
    Menu,
    X
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
    const [sidebarOpen, setSidebarOpen] = useState(false);

    useEffect(() => {
        setIsMounted(true);
        const token = localStorage.getItem('access_token');
        if (!token && !pathname.includes('/login') && !pathname.includes('/register')) {
            router.push('/login');
        }
    }, [pathname, router]);

    // Close sidebar when navigating
    useEffect(() => {
        setSidebarOpen(false);
    }, [pathname]);

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

    const SidebarContent = () => (
        <>
            {/* Logo */}
            <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-[#1f2937] flex-shrink-0">
                <span className="text-xl font-extrabold tracking-tight">
                    <span className="text-gray-900 dark:text-gray-100">Bot</span><span className="text-[#8b5cf6]">fy</span>
                </span>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={`flex items-center px-3 py-2.5 text-sm font-medium rounded-lg group transition ${isActive
                                ? 'bg-blue-50 dark:bg-[#1f2937] text-blue-700 dark:text-white'
                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-[#1f2937] hover:text-gray-900 dark:hover:text-white'
                                }`}
                        >
                            <item.icon
                                className={`mr-3 flex-shrink-0 h-5 w-5 ${isActive ? 'text-[#8b5cf6]' : 'text-gray-500 group-hover:text-gray-300'}`}
                                aria-hidden="true"
                            />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>

            {/* Logout */}
            <div className="p-4 border-t border-gray-200 dark:border-[#1f2937] transition-colors duration-200">
                <button
                    onClick={handleLogout}
                    className="flex w-full items-center px-3 py-2 text-sm font-medium text-red-600 dark:text-red-500 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition"
                >
                    <LogOut className="mr-3 flex-shrink-0 h-5 w-5 text-red-500" />
                    {t.signOut}
                </button>
            </div>
        </>
    );

    return (
        <div className="flex h-screen bg-gray-50 dark:bg-[#0b0e14] transition-colors duration-200 overflow-hidden">

            {/* ── Desktop Sidebar ── */}
            <div className="hidden lg:flex lg:flex-col lg:w-64 bg-white dark:bg-[#111827] border-r border-gray-200 dark:border-[#1f2937] transition-colors duration-200 flex-shrink-0">
                <SidebarContent />
            </div>

            {/* ── Mobile Sidebar Overlay ── */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* ── Mobile Sidebar Drawer ── */}
            <div className={`fixed inset-y-0 left-0 z-50 w-72 flex flex-col bg-white dark:bg-[#111827] border-r border-gray-200 dark:border-[#1f2937] transform transition-transform duration-300 ease-in-out lg:hidden ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
                {/* Close button inside drawer */}
                <button
                    className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-[#1f2937] transition"
                    onClick={() => setSidebarOpen(false)}
                >
                    <X className="h-5 w-5" />
                </button>
                <SidebarContent />
            </div>

            {/* ── Main Content ── */}
            <div className="flex-1 flex flex-col overflow-hidden min-w-0">

                {/* Top bar */}
                <header className="h-14 bg-white dark:bg-[#111827] border-b border-gray-200 dark:border-[#1f2937] flex items-center justify-between px-4 lg:px-6 flex-shrink-0 transition-colors duration-200">
                    {/* Hamburger — mobile only */}
                    <button
                        className="lg:hidden p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-[#1f2937] transition"
                        onClick={() => setSidebarOpen(true)}
                        aria-label="Abrir menu"
                    >
                        <Menu className="h-5 w-5" />
                    </button>

                    {/* Mobile Logo */}
                    <span className="lg:hidden text-lg font-extrabold tracking-tight">
                        <span className="text-gray-900 dark:text-gray-100">Bot</span><span className="text-[#8b5cf6]">fy</span>
                    </span>

                    {/* Desktop spacer */}
                    <div className="hidden lg:block" />

                    {/* Controls */}
                    <div className="flex items-center gap-2">
                        <ThemeToggle />
                        <LanguageSelector />
                    </div>
                </header>

                {/* Page content */}
                <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-gray-50 dark:bg-[#0b0e14] text-gray-900 dark:text-gray-100 transition-colors duration-200">
                    {children}
                </main>
            </div>
        </div>
    );
}
