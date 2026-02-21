"use client";

import React, { useState, useEffect } from 'react';
import { useI18n } from '@/lib/i18n-context';
import { Users, UserPlus, Mail, Shield, Trash2 } from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function TeamPage() {
    const { t } = useI18n();
    const [members, setMembers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchMembers();
    }, []);

    const fetchMembers = async () => {
        try {
            // Simulated for now if endpoint doesn't exist, but typically would be:
            // const res = await apiClient.get('/tenants/members');
            // setMembers(res.data);

            // Placeholder data
            setMembers([
                { id: 1, name: 'Admin User', email: 'admin@botfy.ai', role: 'Admin', status: 'Active' },
                { id: 2, name: 'Support Agent', email: 'support@botfy.ai', role: 'Agent', status: 'Active' }
            ]);
        } catch (err) {
            setError('Failed to load team members');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors duration-200">{t.navTeam || 'Equipe'}</h1>
                    <p className="text-gray-500 dark:text-gray-400 transition-colors duration-200">Gerencie os membros da sua equipe e permissões.</p>
                </div>
                <button className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold shadow-sm">
                    <UserPlus className="h-4 w-4 mr-2" />
                    Convidar Membro
                </button>
            </div>

            <div className="bg-white dark:bg-[#111827] shadow rounded-xl overflow-hidden border border-gray-200 dark:border-[#1f2937] transition-colors duration-200">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-[#1f2937] transition-colors duration-200">
                    <thead className="bg-gray-50 dark:bg-[#0b0e14] transition-colors duration-200">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Membro</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Nível de Acesso</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ações</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-[#111827] divide-y divide-gray-200 dark:divide-[#1f2937] transition-colors duration-200">
                        {members.map((member) => (
                            <tr key={member.id} className="hover:bg-gray-50 dark:hover:bg-[#1f2937]/50 transition">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-700 dark:text-blue-400 font-bold border border-transparent dark:border-blue-900/50 transition-colors duration-200">
                                            {member.name.charAt(0)}
                                        </div>
                                        <div className="ml-4">
                                            <div className="text-sm font-medium text-gray-900 dark:text-white transition-colors duration-200">{member.name}</div>
                                            <div className="text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">{member.email}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 dark:bg-[#1f2937] text-gray-800 dark:text-gray-300 border border-transparent dark:border-gray-700 transition-colors duration-200">
                                        {member.role}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 border border-transparent dark:border-green-900/50 transition-colors duration-200">
                                        {member.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button className="text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition ml-4">
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
