"use client";

import React, { useState, useEffect } from 'react';
import { useI18n } from '@/lib/i18n-context';
import { Users, Shield, Trash2, Clock, AlertCircle, GripVertical } from 'lucide-react';
import { apiClient } from '@/lib/api';

type MemberStatus = 'Pending' | 'Active' | 'Inactive';

interface TeamMember {
    id: number;
    name: string;
    email: string;
    role: string;
    status: MemberStatus;
}

export default function TeamPage() {
    const { t } = useI18n();
    const [members, setMembers] = useState<TeamMember[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [draggedItem, setDraggedItem] = useState<number | null>(null);

    useEffect(() => {
        fetchMembers();
    }, []);

    const fetchMembers = async () => {
        try {
            // Simulated for now if endpoint doesn't exist.
            // When real endpoint is ready, map the backend status to 'Pending' | 'Active' | 'Inactive'
            setMembers([
                { id: 1, name: 'Admin User', email: 'admin@botfy.ai', role: 'Admin', status: 'Active' },
                { id: 2, name: 'Support Agent', email: 'support@botfy.ai', role: 'Agent', status: 'Active' },
                { id: 3, name: 'New Hire', email: 'newhire@botfy.ai', role: 'Viewer', status: 'Pending' },
                { id: 4, name: 'Old Agent', email: 'old@botfy.ai', role: 'Agent', status: 'Inactive' }
            ]);
        } catch (err) {
            setError('Failed to load team members');
        } finally {
            setLoading(false);
        }
    };

    // --- Drag and Drop Handlers ---
    const handleDragStart = (e: React.DragEvent, id: number) => {
        setDraggedItem(id);
        e.dataTransfer.effectAllowed = 'move';
        // Make the drag image slightly transparent
        if (e.target instanceof HTMLElement) {
            e.target.style.opacity = '0.5';
        }
    };

    const handleDragEnd = (e: React.DragEvent) => {
        setDraggedItem(null);
        if (e.target instanceof HTMLElement) {
            e.target.style.opacity = '1';
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault(); // Necessary to allow dropping
        e.dataTransfer.dropEffect = 'move';
    };

    const handleDrop = async (e: React.DragEvent, newStatus: MemberStatus) => {
        e.preventDefault();
        if (draggedItem === null) return;

        // Optimistically update UI
        setMembers(prev => prev.map(m =>
            m.id === draggedItem ? { ...m, status: newStatus } : m
        ));

        // TODO: Call backend to update member status
        // try {
        //     await apiClient.patch(`/tenants/members/${draggedItem}`, { status: newStatus });
        // } catch (err) {
        //     // Revert on failure
        //     fetchMembers();
        // }
    };

    // --- Columns Definition ---
    const columns: { id: MemberStatus; title: string; icon: React.ReactNode; color: string }[] = [
        { id: 'Pending', title: 'Convite Pendente', icon: <Clock className="w-4 h-4" />, color: 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-900/30' },
        { id: 'Active', title: 'Ativos', icon: <Users className="w-4 h-4" />, color: 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-900/30' },
        { id: 'Inactive', title: 'Bloqueados / Inativos', icon: <AlertCircle className="w-4 h-4" />, color: 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900/30' }
    ];

    if (loading) {
        return <div className="p-8 text-center text-gray-500">Carregando equipe...</div>;
    }

    return (
        <div className="max-w-7xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
            <div className="mb-6 flex-shrink-0">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors duration-200">{t.navTeam || 'Equipe'}</h1>
                <p className="text-gray-500 dark:text-gray-400 mt-1 transition-colors duration-200">Arraste os membros entre as colunas para alterar o status de acesso deles.</p>
            </div>

            {/* Kanban Board */}
            <div className="flex-1 flex gap-6 overflow-x-auto pb-4">
                {columns.map(col => (
                    <div
                        key={col.id}
                        className={`flex flex-col w-80 rounded-xl border flex-shrink-0 ${col.color} bg-opacity-50 dark:bg-opacity-50`}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, col.id)}
                    >
                        {/* Column Header */}
                        <div className="p-4 border-b border-inherit flex items-center justify-between">
                            <div className="flex items-center gap-2 font-semibold text-gray-700 dark:text-gray-200">
                                {col.icon}
                                {col.title}
                            </div>
                            <span className="bg-white dark:bg-[#1f2937] text-gray-500 dark:text-gray-400 text-xs font-bold px-2 py-1 rounded-full shadow-sm">
                                {members.filter(m => m.status === col.id).length}
                            </span>
                        </div>

                        {/* Column Content (Cards) */}
                        <div className="flex-1 p-3 flex flex-col gap-3 overflow-y-auto min-h-[150px]">
                            {members.filter(m => m.status === col.id).map(member => (
                                <div
                                    key={member.id}
                                    draggable
                                    onDragStart={(e) => handleDragStart(e, member.id)}
                                    onDragEnd={handleDragEnd}
                                    className="bg-white dark:bg-[#1f2937] border border-gray-200 dark:border-gray-700/60 p-4 rounded-lg shadow-sm cursor-grab active:cursor-grabbing hover:shadow-md hover:border-blue-300 dark:hover:border-blue-500/50 transition-all group"
                                >
                                    <div className="flex justify-between items-start mb-3">
                                        <div className="flex items-center gap-3 overflow-hidden">
                                            <div className="flex-shrink-0 flex items-center justify-center cursor-grab">
                                                <GripVertical className="w-4 h-4 text-gray-300 dark:text-gray-600 group-hover:text-gray-400 dark:group-hover:text-gray-500 transition-colors" />
                                            </div>
                                            <div className="h-9 w-9 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-blue-700 dark:text-blue-400 font-bold flex-shrink-0 border border-transparent dark:border-blue-800/50">
                                                {member.name.charAt(0).toUpperCase()}
                                            </div>
                                            <div className="min-w-0">
                                                <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate" title={member.name}>
                                                    {member.name}
                                                </h3>
                                                <p className="text-xs text-gray-500 dark:text-gray-400 truncate" title={member.email}>
                                                    {member.email}
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between mt-2 pt-3 border-t border-gray-100 dark:border-gray-700/50 pl-6">
                                        <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-[10px] font-medium text-gray-600 dark:text-gray-300">
                                            <Shield className="w-3 h-3" />
                                            {member.role}
                                        </div>
                                        <button
                                            className="text-gray-400 hover:text-red-500 dark:text-gray-500 dark:hover:text-red-400 transition-colors p-1 rounded"
                                            title="Remover Membro"
                                            onClick={(e) => {
                                                e.stopPropagation(); // Prevent drag interference
                                                // Handle delete
                                                setMembers(prev => prev.filter(m => m.id !== member.id));
                                            }}
                                        >
                                            <Trash2 className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                </div>
                            ))}

                            {/* Empty state zone to make dropping easier when column is empty */}
                            {members.filter(m => m.status === col.id).length === 0 && (
                                <div className="flex-1 flex items-center justify-center border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-lg text-gray-400 dark:text-gray-500 text-sm">
                                    Solte um card aqui
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
