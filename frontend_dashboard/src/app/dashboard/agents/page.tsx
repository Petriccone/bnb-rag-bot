"use client";

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { useI18n } from '@/lib/i18n-context';
import Link from 'next/link';
import { Plus, Trash2, Settings } from 'lucide-react';

interface Agent {
    id: string;
    name: string;
    niche: string;
    status: string;
}

export default function AgentsPage() {
    const { t } = useI18n();
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchAgents = async () => {
        try {
            const tenant_id = localStorage.getItem('tenant_id');
            const res = await apiClient.get('/agents/', { headers: { 'x-tenant-id': tenant_id } });
            setAgents(res.data);
        } catch { /* backend offline */ } finally { setLoading(false); }
    };

    useEffect(() => { fetchAgents(); }, []);

    const handleDelete = async (id: string) => {
        if (!confirm(t.confirmDelete)) return;
        try {
            const tenant_id = localStorage.getItem('tenant_id');
            await apiClient.delete(`/agents/${id}`, { headers: { 'x-tenant-id': tenant_id } });
            setAgents(agents.filter(a => a.id !== id));
        } catch { /* error */ }
    };

    return (
        <div className="max-w-7xl mx-auto">
            <div className="md:flex md:items-center md:justify-between">
                <div className="flex-1 min-w-0">
                    <h2 className="text-2xl font-bold leading-7 text-gray-900 dark:text-white transition-colors duration-200">{t.agentsTitle}</h2>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">{t.agentsDescription}</p>
                </div>
                <div className="mt-4 flex md:mt-0 md:ml-4">
                    <Link href="/dashboard/agents/new"
                        className="inline-flex items-center justify-center rounded-lg border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 transition">
                        <Plus className="h-4 w-4 mr-2" />{t.newAgent}
                    </Link>
                </div>
            </div>

            <div className="mt-8 bg-white dark:bg-[#111827] shadow overflow-hidden rounded-lg border border-transparent dark:border-[#1f2937] transition-colors duration-200">
                {loading ? (
                    <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-500"></div></div>
                ) : agents.length === 0 ? (
                    <div className="text-center py-12"><p className="text-sm text-gray-500 dark:text-gray-400">{t.noAgentsFound}</p></div>
                ) : (
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-[#1f2937] transition-colors duration-200">
                        <thead className="bg-gray-50 dark:bg-[#0b0e14] transition-colors duration-200">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t.agentName}</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t.specialty}</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t.status}</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t.actions}</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-[#111827] divide-y divide-gray-200 dark:divide-[#1f2937] transition-colors duration-200">
                            {agents.map((agent) => (
                                <tr key={agent.id} className="hover:bg-gray-50 dark:hover:bg-[#1f2937] transition-colors duration-200">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100 transition-colors duration-200">{agent.name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">{agent.niche || t.generalist}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`inline-flex px-2 text-xs leading-5 font-semibold rounded-full border border-transparent dark:border-opacity-50 transition-colors duration-200 ${agent.status === 'active' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 dark:border-green-800/50' : 'bg-gray-100 dark:bg-[#1f2937] text-gray-800 dark:text-gray-400 dark:border-[#374151]'}`}>
                                            {agent.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <Link href={`/dashboard/agents/${agent.id}`} className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 inline-flex items-center mr-3 transition-colors duration-200">
                                            <Settings className="h-4 w-4 mr-1" />{t.edit}
                                        </Link>
                                        <button onClick={() => handleDelete(agent.id)} className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 inline-flex items-center transition-colors duration-200">
                                            <Trash2 className="h-4 w-4 mr-1" />{t.delete}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
