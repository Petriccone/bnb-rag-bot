"use client";

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { useI18n } from '@/lib/i18n-context';
import { Activity, MessageSquare, Database, Zap, Bot } from 'lucide-react';

interface UsageSummary {
    plan: string;
    messages_used: number;
    messages_limit: number | null;
    tokens_used: number;
    tokens_limit: number | null;
    storage_mb: number;
    storage_limit_mb: number | null;
}

export default function DashboardHome() {
    const { t } = useI18n();
    const [usage, setUsage] = useState<UsageSummary | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchUsage = async () => {
            try {
                const tenant_id = localStorage.getItem('tenant_id');
                const res = await apiClient.get('/usage', { headers: { 'x-tenant-id': tenant_id } });
                setUsage(res.data);
            } catch { /* backend offline */ } finally { setLoading(false); }
        };
        fetchUsage();
    }, []);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    const stats = [
        { name: t.activePlan, stat: usage?.plan?.toUpperCase() || 'FREE', icon: Zap },
        { name: t.messagesSent, stat: `${usage?.messages_used || 0} / ${usage?.messages_limit || '∞'}`, icon: MessageSquare },
        { name: t.tokensProcessed, stat: `${(usage?.tokens_used || 0).toLocaleString()}`, icon: Activity },
        { name: t.vectorStorage, stat: `${(usage?.storage_mb || 0).toFixed(2)} MB / ${usage?.storage_limit_mb || '∞'} MB`, icon: Database },
    ];

    return (
        <div className="max-w-7xl mx-auto">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white transition-colors duration-200">{t.dashboardTitle}</h1>

            <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                {stats.map((item) => (
                    <div key={item.name} className="relative bg-white dark:bg-[#111827] pt-5 px-4 pb-12 sm:pt-6 sm:px-6 shadow rounded-lg border border-gray-200 dark:border-[#1f2937] overflow-hidden transition-colors duration-200">
                        <dt>
                            <div className="absolute bg-[#8b5cf6] rounded-md p-3 shadow-sm">
                                <item.icon className="h-6 w-6 text-white" aria-hidden="true" />
                            </div>
                            <p className="ml-16 text-sm font-medium text-gray-500 dark:text-gray-400 truncate">{item.name}</p>
                        </dt>
                        <dd className="ml-16 pb-6 flex items-baseline sm:pb-7">
                            <p className="text-2xl font-semibold text-gray-900 dark:text-white transition-colors duration-200">{item.stat}</p>
                        </dd>
                    </div>
                ))}
            </div>

            {(!usage || usage?.plan === 'free') && (
                <div className="mt-8 bg-gradient-to-r from-[#8b5cf6] to-[#6d28d9] rounded-xl shadow-lg transform transition-all hover:scale-[1.01]">
                    <div className="px-6 py-8 sm:p-10 lg:flex lg:items-center lg:justify-between">
                        <div>
                            <h3 className="text-2xl font-extrabold text-white sm:text-3xl">{t.upgradeTitle}</h3>
                            <p className="mt-4 text-lg text-purple-100 max-w-2xl">{t.upgradeDescription}</p>
                        </div>
                        <div className="mt-8 lg:mt-0 lg:flex-shrink-0">
                            <a href="/dashboard/billing" className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-[#6d28d9] bg-white hover:bg-gray-50 transition">
                                {t.upgradeCta}
                            </a>
                        </div>
                    </div>
                </div>
            )}

            <div className="mt-8 bg-white dark:bg-[#111827] border border-gray-200 dark:border-[#1f2937] shadow-xl rounded-xl p-8 transition-colors duration-200">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6 transition-colors duration-200">{t.quickActions}</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <button onClick={() => window.location.href = '/dashboard/agents'}
                        className="group relative border-2 border-gray-200 dark:border-[#8b5cf6] bg-gray-50 dark:bg-[#0b0e14]/50 rounded-xl p-6 flex flex-col items-center justify-center hover:bg-purple-50 dark:hover:bg-[#8b5cf6]/10 hover:border-purple-300 dark:hover:border-[#a78bfa] transition-all duration-200 dark:shadow-[0_0_15px_rgba(139,92,246,0.15)] dark:hover:shadow-[0_0_25px_rgba(139,92,246,0.3)] w-full">
                        <div className="absolute inset-0 bg-gradient-to-br from-purple-100/50 dark:from-[#8b5cf6]/5 to-transparent rounded-xl pointer-events-none"></div>
                        <Bot className="h-10 w-10 text-[#8b5cf6] mb-3 group-hover:scale-110 transition-transform duration-200" />
                        <span className="text-base font-bold text-gray-900 dark:text-white group-hover:text-purple-700 dark:group-hover:text-[#a78bfa] transition-colors">{t.createNewAgent}</span>
                        <span className="text-sm text-gray-500 dark:text-gray-400 mt-2 text-center group-hover:text-purple-600 dark:group-hover:text-gray-300 transition-colors">{t.createNewAgentDesc}</span>
                    </button>
                </div>
            </div>
        </div>
    );
}
