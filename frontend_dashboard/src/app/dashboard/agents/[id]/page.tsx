"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useI18n } from '@/lib/i18n-context';
import { Save, Sparkles, Loader2, UploadCloud, FileText, CheckCircle, GitBranch, ArrowRight } from 'lucide-react';

export default function AgentEditPage() {
    const router = useRouter();
    const params = useParams();
    const { t } = useI18n();

    // id always available from url
    const id = params?.id as string;

    const [name, setName] = useState('');
    const [niche, setNiche] = useState('');
    const [prompt, setPrompt] = useState('');
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);
    const [error, setError] = useState('');
    const [namespace, setNamespace] = useState('');

    // RAG Upload States
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);

    // AI Generator States
    const [showAiGen, setShowAiGen] = useState(false);
    const [genLoading, setGenLoading] = useState(false);
    const [aiContext, setAiContext] = useState('');
    const [aiAudience, setAiAudience] = useState('');
    const [aiTone, setAiTone] = useState('');
    const [aiGoal, setAiGoal] = useState('');

    // Agent-to-agent delegation
    const [allAgents, setAllAgents] = useState<{ id: string; name: string; niche: string }[]>([]);
    const [canDelegateTo, setCanDelegateTo] = useState<string[]>([]);

    useEffect(() => {
        const fetchAgent = async () => {
            if (!id) return;
            try {
                const tenant_id = localStorage.getItem('tenant_id');
                // Fetch this agent
                const res = await apiClient.get(`/agents/${id}`, { headers: { 'x-tenant-id': tenant_id } });
                setName(res.data.name || '');
                setNiche(res.data.niche || '');
                setPrompt(res.data.prompt_custom || '');
                setNamespace(res.data.embedding_namespace || '');
                // Load can_delegate_to from settings
                const delegateTo = res.data.settings?.can_delegate_to;
                if (Array.isArray(delegateTo)) setCanDelegateTo(delegateTo);

                // Fetch all agents for delegation UI
                const allRes = await apiClient.get('/agents/', { headers: { 'x-tenant-id': tenant_id } });
                setAllAgents((allRes.data || []).filter((a: any) => a.id !== id));
            } catch (err: any) {
                setError((t as any).agentNotFound || "Agente não encontrado");
            } finally {
                setFetching(false);
            }
        };
        fetchAgent();
    }, [id, t]);

    const toggleDelegate = (agentId: string) => {
        setCanDelegateTo(prev =>
            prev.includes(agentId) ? prev.filter(x => x !== agentId) : [...prev, agentId]
        );
    };

    const handleGenerateAiPrompt = async () => {
        setGenLoading(true);
        try {
            const res = await apiClient.post('/agents/generate-prompt', {
                context: aiContext,
                audience: aiAudience,
                tone: aiTone,
                goal: aiGoal
            });
            setPrompt(res.data.prompt);
            setShowAiGen(false);
        } catch (err: any) {
            setError("Falha ao gerar prompt por IA");
        } finally {
            setGenLoading(false);
        }
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        try {
            setUploading(true);
            setUploadSuccess(false);

            // Make sure the agent has a namespace generated on the fly if needed
            let currentNamespace = namespace;
            if (!currentNamespace) {
                currentNamespace = `agent_${id}`;
                await apiClient.patch(`/agents/${id}`, { embedding_namespace: currentNamespace });
                setNamespace(currentNamespace);
            }

            const formData = new FormData();
            formData.append('file', file);

            const uploadUrl = `/documents/upload?embedding_namespace=${encodeURIComponent(currentNamespace)}`;

            const response = await apiClient.post(uploadUrl, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (response.status === 200 || response.status === 201) {
                setUploadSuccess(true);
                setTimeout(() => setUploadSuccess(false), 5000);
            } else {
                alert("Erro ao enviar o documento.");
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            alert("Erro ao enviar o documento.");
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const tenant_id = localStorage.getItem('tenant_id');
            await apiClient.patch(`/agents/${id}`, {
                name,
                niche,
                prompt_custom: prompt,
                settings: { can_delegate_to: canDelegateTo },
            }, { headers: { 'x-tenant-id': tenant_id } });
            router.push('/dashboard/agents');
        } catch (err: any) {
            setError(err.response?.data?.detail || "Falha ao atualizar agente");
        } finally { setLoading(false); }
    };

    if (fetching) {
        return (
            <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600 dark:text-blue-500" />
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto py-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors duration-200">{(t as any).editAgentTitle || "Editar Agente"}</h2>

            {error && (
                <div className="bg-red-50 border-l-4 border-red-400 p-4 mt-4 rounded"><p className="text-sm text-red-700">{error}</p></div>
            )}

            <form onSubmit={handleSave} className="mt-6 space-y-8 divide-y divide-gray-200 dark:divide-[#1f2937] bg-white dark:bg-[#111827] p-8 shadow rounded-lg border border-transparent dark:border-[#1f2937] transition-colors duration-200">
                <div className="space-y-6">
                    <div>
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white transition-colors duration-200">{(t as any).agentProfile || "Perfil do Agente"}</h3>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">{(t as any).agentProfileDesc || "Atualize as informações do seu agente de IA."}</p>
                    </div>

                    <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 dark:sm:border-[#1f2937] sm:pt-5 transition-colors duration-200">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 sm:mt-px sm:pt-2 transition-colors duration-200">{t.agentName}</label>
                        <div className="mt-1 sm:mt-0 sm:col-span-2">
                            <input type="text" required value={name} onChange={e => setName(e.target.value)}
                                className="max-w-lg block w-full shadow-sm focus:ring-2 focus:ring-blue-600 focus:border-blue-600 sm:max-w-xs sm:text-sm border-gray-300 dark:border-[#374151] rounded-lg py-2 px-3 border bg-white dark:bg-[#0b0e14] text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors duration-200"
                                placeholder={t.agentNamePlaceholder} />
                        </div>
                    </div>

                    <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 dark:sm:border-[#1f2937] sm:pt-5 transition-colors duration-200">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 sm:mt-px sm:pt-2 transition-colors duration-200">{t.specialty}</label>
                        <div className="mt-1 sm:mt-0 sm:col-span-2">
                            <input type="text" required value={niche} onChange={e => setNiche(e.target.value)}
                                className="max-w-lg block w-full shadow-sm focus:ring-2 focus:ring-blue-600 focus:border-blue-600 sm:max-w-xs sm:text-sm border-gray-300 dark:border-[#374151] rounded-lg py-2 px-3 border bg-white dark:bg-[#0b0e14] text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors duration-200"
                                placeholder={t.specialtyPlaceholder} />
                            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">{t.specialtyHelp}</p>
                        </div>
                    </div>

                    <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 dark:sm:border-[#1f2937] sm:pt-5 transition-colors duration-200">
                        <div className="flex flex-col">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 sm:mt-px sm:pt-2 transition-colors duration-200">{t.customPrompt}</label>
                            <button
                                type="button"
                                onClick={() => setShowAiGen(!showAiGen)}
                                className="mt-4 inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-semibold rounded-full shadow-sm text-white bg-purple-600 hover:bg-purple-700 transition"
                            >
                                <Sparkles className="h-3 w-3 mr-1" />
                                {showAiGen ? "Fechar Gerador" : "Criar prompt com IA"}
                            </button>
                        </div>
                        <div className="mt-1 sm:mt-0 sm:col-span-2 space-y-4">
                            {showAiGen && (
                                <div className="bg-white dark:bg-[#0b0e14] p-6 rounded-xl border-2 border-purple-400 space-y-6 shadow-xl mb-8 transition-colors duration-200">
                                    <div className="flex items-center justify-between border-b border-purple-100 dark:border-purple-900/30 pb-4">
                                        <h4 className="text-lg font-black text-purple-900 dark:text-purple-300 flex items-center transition-colors duration-200">
                                            <Sparkles className="h-6 w-6 mr-3 text-purple-600 dark:text-purple-400" />
                                            Gerador de Prompt Mágico (IA)
                                        </h4>
                                        <span className="text-[11px] bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-300 px-3 py-1 rounded-full font-black uppercase tracking-tighter transition-colors duration-200">Powered by GPT-4</span>
                                    </div>

                                    <div className="grid grid-cols-1 gap-6">
                                        <div className="space-y-2">
                                            <label className="text-[11px] font-black text-gray-900 dark:text-gray-300 uppercase tracking-widest flex items-center transition-colors duration-200">
                                                Contexto da Empresa
                                                <span className="text-red-600 dark:text-red-500 ml-1 text-base">*</span>
                                            </label>
                                            <input
                                                type="text"
                                                placeholder="Ex: Agência de intercâmbio para a Irlanda"
                                                value={aiContext}
                                                onChange={e => setAiContext(e.target.value)}
                                                className="w-full text-base rounded-xl border-2 border-gray-300 dark:border-[#374151] focus:border-purple-600 focus:ring-4 focus:ring-purple-50 dark:focus:ring-purple-900/20 py-4 px-5 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 bg-gray-50 dark:bg-[#111827] font-bold transition-all shadow-inner"
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <label className="text-[11px] font-black text-gray-900 dark:text-gray-300 uppercase tracking-widest transition-colors duration-200">Público-alvo / Nicho</label>
                                            <input
                                                type="text"
                                                placeholder="Ex: Estudantes de 20-30 anos buscando visto"
                                                value={aiAudience}
                                                onChange={e => setAiAudience(e.target.value)}
                                                className="w-full text-base rounded-xl border-2 border-gray-300 dark:border-[#374151] focus:border-purple-600 focus:ring-4 focus:ring-purple-50 dark:focus:ring-purple-900/20 py-4 px-5 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 bg-gray-50 dark:bg-[#111827] font-bold transition-all shadow-inner"
                                            />
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div className="space-y-2">
                                                <label className="text-[11px] font-black text-gray-900 dark:text-gray-300 uppercase tracking-widest transition-colors duration-200">Tom de Voz</label>
                                                <input
                                                    type="text"
                                                    placeholder="Ex: Prestativo e entusiasmado"
                                                    value={aiTone}
                                                    onChange={e => setAiTone(e.target.value)}
                                                    className="w-full text-base rounded-xl border-2 border-gray-300 dark:border-[#374151] focus:border-purple-600 focus:ring-4 focus:ring-purple-50 dark:focus:ring-purple-900/20 py-4 px-5 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 bg-gray-50 dark:bg-[#111827] font-bold transition-all shadow-inner"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[11px] font-black text-gray-900 dark:text-gray-300 uppercase tracking-widest transition-colors duration-200">Objetivo Final</label>
                                                <input
                                                    type="text"
                                                    placeholder="Ex: Agendar consultoria gratuita"
                                                    value={aiGoal}
                                                    onChange={e => setAiGoal(e.target.value)}
                                                    className="w-full text-base rounded-xl border-2 border-gray-300 dark:border-[#374151] focus:border-purple-600 focus:ring-4 focus:ring-purple-50 dark:focus:ring-purple-900/20 py-4 px-5 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 bg-gray-50 dark:bg-[#111827] font-bold transition-all shadow-inner"
                                                />
                                            </div>
                                        </div>

                                        <button
                                            type="button"
                                            disabled={genLoading || !aiContext}
                                            onClick={handleGenerateAiPrompt}
                                            className="w-full bg-purple-800 text-white rounded-2xl py-5 text-base font-black hover:bg-black hover:scale-[1.02] disabled:bg-gray-300 disabled:scale-100 transition-all duration-300 shadow-2xl flex justify-center items-center group relative overflow-hidden"
                                        >
                                            {genLoading ? (
                                                <div className="flex items-center">
                                                    <svg className="animate-spin -ml-1 mr-3 h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                    </svg>
                                                    <span className="tracking-[2px]">CRIANDO PROMPT MÁGICO...</span>
                                                </div>
                                            ) : (
                                                <span className="flex items-center tracking-[1.5px]">
                                                    GERAR PROMPT AGORA
                                                    <Sparkles className="ml-3 h-5 w-5 group-hover:rotate-45 transition-transform" />
                                                </span>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            )}
                            <textarea rows={5} value={prompt} onChange={e => setPrompt(e.target.value)}
                                className="max-w-lg shadow-sm block w-full focus:ring-2 focus:ring-blue-600 focus:border-blue-600 sm:text-sm border border-gray-300 dark:border-[#374151] bg-white dark:bg-[#0b0e14] text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 rounded-lg py-2 px-3 transition-colors duration-200"
                                placeholder={t.customPromptPlaceholder} />
                            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">{t.customPromptHelp}</p>
                        </div>
                    </div>

                    {/* Agent-to-Agent Delegation Section */}
                    <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 dark:sm:border-[#1f2937] sm:pt-5 transition-colors duration-200">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 transition-colors duration-200 flex items-center gap-1.5">
                                <GitBranch className="h-4 w-4 text-indigo-500" />
                                Pode Chamar
                            </label>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Agentes que este agente pode acionar automaticamente.</p>
                        </div>
                        <div className="mt-1 sm:mt-0 sm:col-span-2 space-y-3">
                            {allAgents.length === 0 ? (
                                <p className="text-sm text-gray-400 dark:text-gray-500 italic">Nenhum outro agente disponível no tenant.</p>
                            ) : (
                                <>
                                    <div className="space-y-2">
                                        {allAgents.map(agent => (
                                            <label
                                                key={agent.id}
                                                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all duration-150 ${canDelegateTo.includes(agent.id)
                                                    ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20 dark:border-indigo-600'
                                                    : 'border-gray-200 dark:border-[#374151] hover:border-gray-300 dark:hover:border-gray-500'
                                                    }`}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={canDelegateTo.includes(agent.id)}
                                                    onChange={() => toggleDelegate(agent.id)}
                                                    className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                                                />
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{agent.name}</p>
                                                    {agent.niche && <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{agent.niche}</p>}
                                                </div>
                                                {canDelegateTo.includes(agent.id) && (
                                                    <span className="flex-shrink-0 text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-100 dark:bg-indigo-900/40 px-2 py-0.5 rounded-full">Ativo</span>
                                                )}
                                            </label>
                                        ))}
                                    </div>

                                    {/* Visual pipeline */}
                                    {canDelegateTo.length > 0 && (
                                        <div className="mt-3 p-3 bg-gray-50 dark:bg-[#0b0e14] rounded-lg border border-gray-200 dark:border-[#1f2937]">
                                            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest mb-2">Pipeline de delegação</p>
                                            <div className="flex flex-wrap items-center gap-2">
                                                <span className="px-2.5 py-1 rounded-full bg-blue-600 text-white text-xs font-bold shadow">{name || 'Este agente'}</span>
                                                {allAgents.filter(a => canDelegateTo.includes(a.id)).map(a => (
                                                    <React.Fragment key={a.id}>
                                                        <ArrowRight className="h-3.5 w-3.5 text-gray-400 flex-shrink-0" />
                                                        <span className="px-2.5 py-1 rounded-full bg-indigo-600 text-white text-xs font-bold shadow">{a.name}</span>
                                                    </React.Fragment>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                            <p className="text-xs text-gray-400 dark:text-gray-500">
                                O supervisor de IA decide automaticamente quando acionar o agente correto com base na intenção do usuário.
                            </p>
                        </div>
                    </div>

                    {/* RAG Section */}
                    <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 dark:sm:border-[#1f2937] sm:pt-5 transition-colors duration-200">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 transition-colors duration-200">Treinamento Específico</label>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Conhecimento exclusivo deste agente.</p>
                        </div>
                        <div className="mt-1 sm:mt-0 sm:col-span-2 space-y-4">
                            <div className="border-2 border-dashed border-gray-300 dark:border-[#374151] rounded-lg p-6 flex flex-col items-center justify-center text-center hover:bg-gray-50 dark:hover:bg-[#1f2937] transition-colors duration-200 cursor-pointer" onClick={handleUploadClick}>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    className="hidden"
                                    accept=".pdf,.txt,.docx,.csv"
                                    onChange={handleFileChange}
                                />
                                {uploading ? (
                                    <div className="flex flex-col items-center justify-center space-y-3">
                                        <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
                                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Enviando e treinando IA...</p>
                                    </div>
                                ) : uploadSuccess ? (
                                    <div className="flex flex-col items-center justify-center space-y-3">
                                        <CheckCircle className="h-8 w-8 text-green-500" />
                                        <p className="text-sm font-medium text-green-600 dark:text-green-400">Arquivo Indexado com Sucesso!</p>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center space-y-3">
                                        <div className="w-12 h-12 bg-blue-50 dark:bg-blue-900/20 rounded-full flex items-center justify-center">
                                            <UploadCloud className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-900 dark:text-white">Clique para fazer upload</p>
                                            <p className="text-xs text-gray-500 mt-1">PDF, DOCX, TXT até 10MB</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400">
                                <span className="flex items-center"><FileText className="w-4 h-4 mr-1" /> O arquivo será lido apenas por este agente</span>
                                <a href="/dashboard/training" target="_blank" className="text-blue-600 dark:text-blue-500 hover:underline">Ver todos os arquivos</a>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="pt-5 flex justify-end gap-3">
                    <button type="button" onClick={() => router.back()}
                        className="bg-white dark:bg-[#111827] py-2 px-4 border border-gray-300 dark:border-[#374151] rounded-lg shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#1f2937] transition transition-colors duration-200">
                        {t.cancel}
                    </button>
                    <button type="submit" disabled={loading}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-semibold rounded-lg text-white bg-blue-600 dark:bg-blue-600 hover:bg-blue-700 dark:hover:bg-blue-700 disabled:bg-blue-300 dark:disabled:bg-blue-300/50 transition">
                        <Save className="h-4 w-4 mr-2 mt-0.5" />
                        {loading ? "Atualizando..." : "Atualizar Agente"}
                    </button>
                </div>
            </form>
        </div>
    );
}
