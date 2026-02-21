"use client";

import React, { useState, useEffect } from 'react';
import { useI18n } from '@/lib/i18n-context';
import { Users, Plus, Trash2, Edit2, Shield, Settings2, UserPlus, Loader2, Bot } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Team {
    id: string;
    name: string;
    description: string;
    agents_count: number;
    settings: any;
}

interface Agent {
    id: string;
    name: string;
    niche: string;
    team_id: string | null;
}

export default function TeamPage() {
    const { t } = useI18n();
    const [teams, setTeams] = useState<Team[]>([]);
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal states
    const [isTeamModalOpen, setIsTeamModalOpen] = useState(false);
    const [editingTeam, setEditingTeam] = useState<Team | null>(null);
    const [teamForm, setTeamForm] = useState({ name: '', description: '' });
    const [isSaving, setIsSaving] = useState(false);

    // Agents assignment modal states
    const [isAgentsModalOpen, setIsAgentsModalOpen] = useState(false);
    const [managingTeam, setManagingTeam] = useState<Team | null>(null);
    const [AssignLoading, setAssignLoading] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [teamsRes, agentsRes] = await Promise.all([
                apiClient.get('/teams'),
                apiClient.get('/agents')
            ]);
            setTeams(teamsRes.data);
            setAgents(agentsRes.data);
        } catch (error) {
            console.error('Error fetching teams:', error);
            // Fallback for demo
        } finally {
            setLoading(false);
        }
    };

    const handleSaveTeam = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSaving(true);
        try {
            if (editingTeam) {
                await apiClient.patch(`/teams/${editingTeam.id}`, teamForm);
            } else {
                await apiClient.post('/teams', teamForm);
            }
            await fetchData();
            setIsTeamModalOpen(false);
        } catch (error) {
            alert('Erro ao salvar equipe');
        } finally {
            setIsSaving(false);
        }
    };

    const handleDeleteTeam = async (teamId: string) => {
        if (!confirm('Tem certeza que deseja excluir esta equipe? Os agentes não serão excluídos, apenas removidos da equipe.')) return;
        try {
            await apiClient.delete(`/teams/${teamId}`);
            await fetchData();
        } catch (error) {
            alert('Erro ao excluir equipe');
        }
    };

    const handleToggleAgentTeam = async (agentId: string, isInTeam: boolean) => {
        if (!managingTeam) return;
        setAssignLoading(true);
        try {
            const newTeamId = isInTeam ? null : managingTeam.id;
            await apiClient.patch(`/agents/${agentId}`, { team_id: newTeamId });
            // Optimistic UI update
            setAgents(prev => prev.map(a => a.id === agentId ? { ...a, team_id: newTeamId } : a));
            // Update team count optimistically
            setTeams(prev => prev.map(t =>
                t.id === managingTeam.id
                    ? { ...t, agents_count: t.agents_count + (isInTeam ? -1 : 1) }
                    : t
            ));
        } catch (error) {
            alert('Erro ao atualizar agente');
            await fetchData(); // Revert on error
        } finally {
            setAssignLoading(false);
        }
    };

    const handleToggleLeader = async (agentId: string) => {
        if (!managingTeam) return;
        setAssignLoading(true);
        try {
            const isRemoving = managingTeam.settings?.leader_agent_id === agentId;
            const newSettings = {
                ...(managingTeam.settings || {}),
                leader_agent_id: isRemoving ? null : agentId
            };

            await apiClient.patch(`/teams/${managingTeam.id}`, { settings: newSettings });

            // Update local state
            setTeams(prev => prev.map(t =>
                t.id === managingTeam.id ? { ...t, settings: newSettings } : t
            ));
            setManagingTeam(prev => prev ? { ...prev, settings: newSettings } : null);
        } catch (error) {
            alert('Erro ao definir líder');
        } finally {
            setAssignLoading(true); // Wait for fetchData to be sure
            await fetchData();
            setAssignLoading(false);
        }
    };

    const openCreateModal = () => {
        setEditingTeam(null);
        setTeamForm({ name: '', description: '' });
        setIsTeamModalOpen(true);
    };

    const openEditModal = (team: Team) => {
        setEditingTeam(team);
        setTeamForm({ name: team.name, description: team.description || '' });
        setIsTeamModalOpen(true);
    };

    const openAgentsModal = (team: Team) => {
        setManagingTeam(team);
        setIsAgentsModalOpen(true);
    };

    if (loading) {
        return <div className="p-8 text-center text-gray-500 flex justify-center"><Loader2 className="w-8 h-8 animate-spin" /></div>;
    }

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Equipes de Agentes</h1>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        Agrupe seus agentes de IA em departamentos ou fluxos de atendimento específicos (Ex: Vendas, Suporte).
                    </p>
                </div>
                <button
                    onClick={openCreateModal}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Nova Equipe
                </button>
            </div>

            {teams.length === 0 ? (
                <div className="bg-white dark:bg-[#111827] border border-gray-200 dark:border-[#1f2937] rounded-xl p-12 text-center">
                    <Users className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Nenhuma equipe criada</h3>
                    <p className="text-gray-500 dark:text-gray-400 mb-6">Comece criando sua primeira equipe para organizar seus agentes de IA.</p>
                    <button onClick={openCreateModal} className="text-blue-600 hover:text-blue-700 font-medium">
                        + Criar primeira equipe
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {teams.map(team => (
                        <div key={team.id} className="bg-white dark:bg-[#111827] border border-gray-200 dark:border-[#1f2937] rounded-xl overflow-hidden hover:shadow-md transition-shadow">
                            <div className="p-5 border-b border-gray-100 dark:border-[#1f2937]">
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="text-lg font-bold text-gray-900 dark:text-white truncate pr-2" title={team.name}>{team.name}</h3>
                                    <div className="flex items-center gap-1 -mt-1 -mr-1">
                                        <button onClick={() => openEditModal(team)} className="p-1.5 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors rounded">
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button onClick={() => handleDeleteTeam(team.id)} className="p-1.5 text-gray-400 hover:text-red-500 transition-colors rounded">
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 h-10">
                                    {team.description || 'Sem descrição'}
                                </p>
                            </div>

                            <div className="bg-gray-50 dark:bg-[#0b0e14] p-4">
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                                        Agentes na equipe
                                    </span>
                                    <span className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs font-bold px-2 py-0.5 rounded-full">
                                        {team.agents_count}
                                    </span>
                                </div>

                                {team.settings?.leader_agent_id && (
                                    <div className="mb-3 flex items-center gap-1.5 text-xs font-medium text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 px-2 py-1 rounded">
                                        <Shield className="w-3 h-4" />
                                        <span>Líder: {agents.find(a => a.id === team.settings.leader_agent_id)?.name || 'Agente não encontrado'}</span>
                                    </div>
                                )}

                                <div className="space-y-2 mb-4">
                                    {agents.filter(a => a.team_id === team.id).slice(0, 3).map(agent => (
                                        <div key={agent.id} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-[#1f2937] border border-gray-200 dark:border-gray-700 px-3 py-2 rounded-md">
                                            <Bot className="w-4 h-4 text-blue-500 shrink-0" />
                                            <span className="truncate">{agent.name}</span>
                                        </div>
                                    ))}
                                    {team.agents_count > 3 && (
                                        <div className="text-xs text-center text-gray-500">
                                            + {team.agents_count - 3} agentes ocultos
                                        </div>
                                    )}
                                    {team.agents_count === 0 && (
                                        <div className="text-sm text-center text-gray-400 dark:text-gray-500 py-2 border border-dashed border-gray-300 dark:border-gray-700 rounded-md">
                                            Equipe vazia
                                        </div>
                                    )}
                                </div>

                                <button
                                    onClick={() => openAgentsModal(team)}
                                    className="w-full bg-white dark:bg-[#1f2937] border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
                                >
                                    <UserPlus className="w-4 h-4" />
                                    Gerenciar Agentes
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Create/Edit Team Modal */}
            {isTeamModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white dark:bg-[#1f2937] rounded-xl w-full max-w-md overflow-hidden shadow-xl">
                        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-[#111827]">
                            <h3 className="font-bold text-lg text-gray-900 dark:text-white">
                                {editingTeam ? 'Editar Equipe' : 'Nova Equipe'}
                            </h3>
                            <button onClick={() => setIsTeamModalOpen(false)} className="text-gray-400 hover:text-gray-500">×</button>
                        </div>
                        <form onSubmit={handleSaveTeam} className="p-6">
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome da Equipe</label>
                                    <input
                                        required
                                        type="text"
                                        className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-[#0b0e14] text-gray-900 dark:text-white"
                                        value={teamForm.name}
                                        onChange={e => setTeamForm({ ...teamForm, name: e.target.value })}
                                        placeholder="Ex: Equipe de Vendas"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
                                    <textarea
                                        className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-[#0b0e14] text-gray-900 dark:text-white h-24 resize-none"
                                        value={teamForm.description}
                                        onChange={e => setTeamForm({ ...teamForm, description: e.target.value })}
                                        placeholder="Descreva o propósito desta equipe..."
                                    />
                                </div>
                            </div>
                            <div className="mt-6 flex justify-end gap-3">
                                <button type="button" onClick={() => setIsTeamModalOpen(false)} className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium">Cancelar</button>
                                <button type="submit" disabled={isSaving} className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 flex items-center gap-2">
                                    {isSaving && <Loader2 className="w-4 h-4 animate-spin" />}
                                    Salvar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Manage Agents Modal */}
            {isAgentsModalOpen && managingTeam && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white dark:bg-[#1f2937] rounded-xl w-full max-w-2xl overflow-hidden shadow-xl flex flex-col max-h-[90vh]">
                        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-[#111827]">
                            <div>
                                <h3 className="font-bold text-lg text-gray-900 dark:text-white">Gerenciar Agentes</h3>
                                <p className="text-sm text-gray-500">Equipe: <span className="font-semibold text-blue-600">{managingTeam.name}</span></p>
                            </div>
                            <button onClick={() => setIsAgentsModalOpen(false)} className="text-gray-400 hover:text-gray-500 text-2xl leading-none">×</button>
                        </div>

                        <div className="p-0 overflow-y-auto flex-1 bg-gray-50/50 dark:bg-[#0b0e14]">
                            <ul className="divide-y divide-gray-200 dark:divide-gray-800">
                                {agents.map(agent => {
                                    const isInThisTeam = agent.team_id === managingTeam.id;
                                    const isInOtherTeam = agent.team_id && agent.team_id !== managingTeam.id;
                                    const otherTeamName = isInOtherTeam ? teams.find(t => t.id === agent.team_id)?.name : null;

                                    return (
                                        <li key={agent.id} className={`p-4 flex items-center justify-between transition-colors ${isInThisTeam ? 'bg-blue-50/50 dark:bg-blue-900/10' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'}`}>
                                            <div className="flex items-center gap-4">
                                                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isInThisTeam ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400' : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}`}>
                                                    <Bot className="w-5 h-5" />
                                                </div>
                                                <div>
                                                    <p className="font-semibold text-gray-900 dark:text-white">{agent.name}</p>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400">{agent.niche || 'Geral'}</p>
                                                    {isInOtherTeam && (
                                                        <p className="text-xs text-orange-600 dark:text-orange-400 mt-0.5">
                                                            Atualmente na equipe: {otherTeamName}
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {isInThisTeam && (
                                                    <button
                                                        onClick={() => handleToggleLeader(agent.id)}
                                                        className={`p-2 rounded-full transition-colors ${agent.id === managingTeam.settings?.leader_agent_id
                                                            ? 'text-amber-500 bg-amber-100 dark:bg-amber-900/40'
                                                            : 'text-gray-300 hover:text-amber-400'}`}
                                                        title={agent.id === managingTeam.settings?.leader_agent_id ? "Remover Líder" : "Definir como Líder"}
                                                    >
                                                        <Shield className={`w-5 h-5 ${agent.id === managingTeam.settings?.leader_agent_id ? 'fill-current' : ''}`} />
                                                    </button>
                                                )}
                                                <button
                                                    disabled={AssignLoading}
                                                    onClick={() => handleToggleAgentTeam(agent.id, isInThisTeam)}
                                                    className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${isInThisTeam
                                                        ? 'bg-blue-600 border-blue-600 text-white hover:bg-red-600 hover:border-red-600 hover:text-white group relative'
                                                        : 'bg-white dark:bg-[#1f2937] border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400'
                                                        }`}
                                                >
                                                    {isInThisTeam ? (
                                                        <span className="group-hover:hidden">Membro</span>
                                                    ) : 'Adicionar'}
                                                    {isInThisTeam && <span className="hidden group-hover:inline">Remover</span>}
                                                </button>
                                            </div>
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>

                        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1f2937] flex justify-end">
                            <button onClick={() => setIsAgentsModalOpen(false)} className="px-5 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg font-medium transition-colors">
                                Concluir
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
