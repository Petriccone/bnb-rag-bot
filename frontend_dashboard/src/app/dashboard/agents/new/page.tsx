"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useI18n } from '@/lib/i18n-context';
import { Save, Sparkles, UploadCloud, FileText } from 'lucide-react';

export default function AgentCreatePage() {
    const router = useRouter();
    const { t } = useI18n();
    const [name, setName] = useState('');
    const [niche, setNiche] = useState('');
    const [prompt, setPrompt] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // AI Generator States
    const [showAiGen, setShowAiGen] = useState(false);
    const [genLoading, setGenLoading] = useState(false);
    const [aiContext, setAiContext] = useState('');
    const [aiAudience, setAiAudience] = useState('');
    const [aiTone, setAiTone] = useState('');
    const [aiGoal, setAiGoal] = useState('');

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

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const tenant_id = localStorage.getItem('tenant_id');
            const response = await apiClient.post('/agents/', { name, niche, prompt_custom: prompt, status: 'active' }, { headers: { 'x-tenant-id': tenant_id } });

            // Redirect to the edit page of the newly created agent to allow for immediate file upload
            if (response.data && response.data.id) {
                router.push(`/dashboard/agents/${response.data.id}`);
            } else {
                router.push('/dashboard/agents');
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || "Falha ao criar agente");
        } finally { setLoading(false); }
    };

    return (
        <div className="max-w-4xl mx-auto py-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors duration-200">{t.createAgentTitle}</h2>

            {error && (
                <div className="bg-red-50 border-l-4 border-red-400 p-4 mt-4 rounded"><p className="text-sm text-red-700">{error}</p></div>
            )}

            <form onSubmit={handleSave} className="mt-6 space-y-8 divide-y divide-gray-200 dark:divide-[#1f2937] bg-white dark:bg-[#111827] p-8 shadow rounded-lg border border-transparent dark:border-[#1f2937] transition-colors duration-200">
                <div className="space-y-6">
                    <div>
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white transition-colors duration-200">{t.agentProfile}</h3>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200">{t.agentProfileDesc}</p>
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

                    {/* RAG Section Placeholder */}
                    <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 dark:sm:border-[#1f2937] sm:pt-5 transition-colors duration-200 opacity-60">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 transition-colors duration-200">Treinamento Específico</label>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Conhecimento exclusivo deste agente.</p>
                        </div>
                        <div className="mt-1 sm:mt-0 sm:col-span-2 space-y-4">
                            <div className="border-2 border-dashed border-gray-300 dark:border-[#374151] rounded-lg p-6 flex flex-col items-center justify-center text-center bg-gray-50 dark:bg-[#1f2937]/50 transition-colors duration-200 cursor-not-allowed">
                                <div className="flex flex-col items-center justify-center space-y-3">
                                    <div className="w-12 h-12 bg-gray-200 dark:bg-gray-800 rounded-full flex items-center justify-center">
                                        <UploadCloud className="h-6 w-6 text-gray-400 dark:text-gray-500" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-gray-900 dark:text-white">Salve o agente primeiro</p>
                                        <p className="text-xs text-gray-500 mt-1">O upload de arquivos será liberado após a criação.</p>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                                <FileText className="w-4 h-4 mr-1" /> O arquivo será lido apenas por este agente
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
                        {loading ? t.saving : t.saveAgent}
                    </button>
                </div>
            </form>
        </div>
    );
}
