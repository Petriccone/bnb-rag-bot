"use client";

import React, { useState, useEffect } from 'react';
import { useI18n } from '@/lib/i18n-context';
import { CheckCircle, XCircle, Loader2, MessageCircle, Send, Globe, Copy, Check } from 'lucide-react';
import { apiClient } from '@/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export default function IntegrationsPage() {
    const { t } = useI18n();
    const [loading, setLoading] = useState(true);

    // WhatsApp State
    const [waStatus, setWaStatus] = useState({ connected: false, message: '' });
    const [waLoading, setWaLoading] = useState(false);

    // Telegram State
    const [tgStatus, setTgStatus] = useState({ connected: false, message: '' });
    const [tgLoading, setTgLoading] = useState(false);
    const [tgToken, setTgToken] = useState('');

    // Widget State
    const [agents, setAgents] = useState<{ id: string; name: string; niche: string }[]>([]);
    const [selectedAgentId, setSelectedAgentId] = useState('');
    const [widgetColor, setWidgetColor] = useState('#2563EB');
    const [widgetPosition, setWidgetPosition] = useState<'right' | 'left'>('right');
    const [copied, setCopied] = useState(false);

    const tenantId = typeof window !== 'undefined' ? localStorage.getItem('tenant_id') || '' : '';

    const fetchStatuses = async () => {
        try {
            setLoading(true);
            try {
                const waRes = await apiClient.get('/whatsapp/status');
                if (waRes.status === 200) setWaStatus({ connected: waRes.data.connected, message: waRes.data.message || 'Desconectado' });
            } catch { /* offline */ }
            try {
                const tgRes = await apiClient.get('/telegram/status');
                if (tgRes.status === 200) setTgStatus({ connected: tgRes.data.connected, message: tgRes.data.error || (tgRes.data.connected ? 'Conectado.' : 'Desconectado. Nenhum bot configurado ou token inválido.') });
                else setTgStatus({ connected: false, message: 'Erro ao buscar status do Telegram' });
            } catch (err: any) { setTgStatus({ connected: false, message: 'Offline: ' + err.message }); }
            try {
                const agRes = await apiClient.get('/agents');
                setAgents(agRes.data || []);
                if (agRes.data?.length > 0) setSelectedAgentId(agRes.data[0].id);
            } catch { /* offline */ }
        } finally { setLoading(false); }
    };

    useEffect(() => { fetchStatuses(); }, []);

    const handleConnectWhatsApp = () => alert('Instruções de conexão do WhatsApp devem ser seguidas conforme a documentação da API (Evolution API ou Meta Cloud).');
    const handleDisconnectWhatsApp = async () => {
        try { setWaLoading(true); await apiClient.delete('/whatsapp/disconnect'); fetchStatuses(); }
        catch { /* error */ } finally { setWaLoading(false); }
    };
    const handleConnectTelegram = async () => {
        if (!tgToken) { alert('Informe o token do Bot do Telegram.'); return; }
        try {
            setTgLoading(true);
            const formData = new FormData();
            formData.append('token_file', new Blob([tgToken], { type: 'text/plain' }), 'token.txt');
            const response = await apiClient.post('/telegram/connect-with-file', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            if (response.status === 200 || response.status === 201) { alert('Telegram conectado com sucesso!'); setTgToken(''); fetchStatuses(); }
            else alert('Erro ao conectar Telegram.');
        } catch { alert('Erro ao conectar Telegram.'); } finally { setTgLoading(false); }
    };

    const backendUrl = API_BASE_URL.replace('/api', '');
    const widgetSnippet = selectedAgentId ? `<script
  src="${backendUrl}/widget.js"
  data-agent-id="${selectedAgentId}"
  data-tenant-id="${tenantId}"
  data-color="${widgetColor}"
  data-position="${widgetPosition}">
</script>` : '';

    const copySnippet = () => {
        navigator.clipboard.writeText(widgetSnippet);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="max-w-6xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Integrações</h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Conecte seus agentes aos canais de comunicação.</p>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center items-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                </div>
            ) : (
                <div className="space-y-6">
                    {/* Channels Row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* WhatsApp Card */}
                        <div className="bg-white dark:bg-[#111827] p-6 shadow-sm rounded-xl border border-gray-200 dark:border-[#1f2937] flex flex-col">
                            <div className="flex items-center mb-4">
                                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mr-4">
                                    <MessageCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-gray-900 dark:text-white">WhatsApp</h2>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Integração oficial Meta ou Evolution API</p>
                                </div>
                            </div>
                            <div className="bg-gray-50 dark:bg-[#0b0e14] border border-gray-100 dark:border-[#1f2937] p-4 rounded-lg mb-6 flex-1">
                                <div className="flex items-center mb-2">
                                    <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 w-24">Status:</span>
                                    {waStatus.connected ? (
                                        <span className="flex items-center text-green-600 dark:text-green-400 text-sm font-medium"><CheckCircle className="h-4 w-4 mr-1" /> Conectado</span>
                                    ) : (
                                        <span className="flex items-center text-gray-500 dark:text-gray-400 text-sm font-medium"><XCircle className="h-4 w-4 mr-1" /> Desconectado</span>
                                    )}
                                </div>
                                <div className="flex items-start">
                                    <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 w-24 mt-0.5">Detalhes:</span>
                                    <span className="text-sm text-gray-700 dark:text-gray-300 flex-1">{waStatus.message}</span>
                                </div>
                            </div>
                            <div className="flex justify-end mt-auto">
                                {waStatus.connected ? (
                                    <button onClick={handleDisconnectWhatsApp} disabled={waLoading} className="px-4 py-2 border border-red-200 text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition text-sm font-medium disabled:opacity-50">
                                        {waLoading ? 'Desconectando...' : 'Desconectar'}
                                    </button>
                                ) : (
                                    <button onClick={handleConnectWhatsApp} disabled={waLoading} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center text-sm font-bold shadow-sm disabled:opacity-50">
                                        Conectar WhatsApp
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Telegram Card */}
                        <div className="bg-white dark:bg-[#111827] p-6 shadow-sm rounded-xl border border-gray-200 dark:border-[#1f2937] flex flex-col">
                            <div className="flex items-center mb-4">
                                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mr-4">
                                    <Send className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-gray-900 dark:text-white">Telegram</h2>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Bot oficial do Telegram</p>
                                </div>
                            </div>
                            <div className="bg-gray-50 dark:bg-[#0b0e14] border border-gray-100 dark:border-[#1f2937] p-4 rounded-lg mb-6 flex-1">
                                <div className="flex items-center mb-2">
                                    <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 w-24">Status:</span>
                                    {tgStatus.connected ? (
                                        <span className="flex items-center text-green-600 dark:text-green-400 text-sm font-medium"><CheckCircle className="h-4 w-4 mr-1" /> Conectado</span>
                                    ) : (
                                        <span className="flex items-center text-gray-500 dark:text-gray-400 text-sm font-medium"><XCircle className="h-4 w-4 mr-1" /> Desconectado</span>
                                    )}
                                </div>
                                <div className="flex items-start">
                                    <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 w-24 mt-0.5">Detalhes:</span>
                                    <span className="text-sm text-gray-700 dark:text-gray-300 flex-1">{tgStatus.message}</span>
                                </div>
                            </div>
                            <div className="flex flex-col gap-3 mt-auto">
                                {!tgStatus.connected && (
                                    <input type="text" placeholder="Cole o token do Bot (BotFather) aqui" value={tgToken} onChange={(e) => setTgToken(e.target.value)}
                                        className="w-full text-sm text-gray-900 dark:text-white bg-white dark:bg-[#0b0e14] border-gray-300 dark:border-[#374151] rounded-lg px-3 py-2 border focus:ring-[#8b5cf6] focus:border-[#8b5cf6] placeholder-gray-400" />
                                )}
                                <div className="flex justify-end">
                                    {tgStatus.connected ? (
                                        <button className="px-4 py-2 border border-red-200 text-red-600 rounded-lg text-sm font-medium opacity-50 cursor-not-allowed">Conectado</button>
                                    ) : (
                                        <button onClick={handleConnectTelegram} disabled={tgLoading || !tgToken} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center text-sm font-bold shadow-sm disabled:opacity-50">
                                            {tgLoading ? 'Conectando...' : 'Conectar Telegram'}
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Website Widget Card — full width */}
                    <div className="bg-white dark:bg-[#111827] rounded-xl border border-gray-200 dark:border-[#1f2937] shadow-sm overflow-hidden">
                        <div className="p-6 border-b border-gray-100 dark:border-[#1f2937]">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                                    <Globe className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-gray-900 dark:text-white">Widget para Website</h2>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Incorpore um chat de IA em qualquer site com uma linha de código.</p>
                                </div>
                                <span className="ml-auto inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800/40">
                                    ✓ Ativo
                                </span>
                            </div>
                        </div>

                        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* Left — Configuração */}
                            <div className="space-y-5">
                                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Configuração</h3>

                                <div>
                                    <label className="block text-sm text-gray-500 dark:text-gray-400 mb-2">Agente</label>
                                    <select value={selectedAgentId} onChange={e => setSelectedAgentId(e.target.value)}
                                        className="w-full bg-white dark:bg-[#0b0e14] border border-gray-300 dark:border-[#374151] text-gray-900 dark:text-white text-sm rounded-lg px-3 py-2.5 focus:ring-purple-500 focus:border-purple-500 outline-none">
                                        {agents.length === 0 && <option value="">Nenhum agente criado</option>}
                                        {agents.map(a => <option key={a.id} value={a.id}>{a.name}{a.niche ? ` — ${a.niche}` : ''}</option>)}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm text-gray-500 dark:text-gray-400 mb-2">Cor do Widget</label>
                                    <div className="flex items-center gap-3">
                                        <input type="color" value={widgetColor} onChange={e => setWidgetColor(e.target.value)}
                                            className="w-10 h-10 rounded-lg border border-gray-300 dark:border-[#374151] bg-transparent cursor-pointer" />
                                        <input type="text" value={widgetColor} onChange={e => setWidgetColor(e.target.value)}
                                            className="flex-1 bg-white dark:bg-[#0b0e14] border border-gray-300 dark:border-[#374151] text-gray-900 dark:text-white text-sm rounded-lg px-3 py-2.5 outline-none font-mono" />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm text-gray-500 dark:text-gray-400 mb-2">Posição</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        {(['right', 'left'] as const).map(pos => (
                                            <button key={pos} onClick={() => setWidgetPosition(pos)}
                                                className={`py-2.5 rounded-lg text-sm font-semibold border transition-all ${widgetPosition === pos ? 'bg-purple-600 border-purple-600 text-white shadow-sm' : 'bg-white dark:bg-[#0b0e14] border-gray-300 dark:border-[#374151] text-gray-500 dark:text-gray-400 hover:border-purple-500 hover:text-purple-600 dark:hover:text-purple-400'}`}>
                                                {pos === 'right' ? '↘ Direita' : '↙ Esquerda'}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Right — Código */}
                            <div className="space-y-5">
                                <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Código de Incorporação</h3>
                                <p className="text-sm text-gray-500 dark:text-gray-400">Cole este código no <code className="text-purple-600 dark:text-purple-300">&lt;body&gt;</code> do seu site, antes de <code className="text-purple-600 dark:text-purple-300">&lt;/body&gt;</code>.</p>

                                {selectedAgentId ? (
                                    <div className="relative">
                                        <pre className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-xs text-green-400 overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed">
                                            {widgetSnippet}
                                        </pre>
                                        <button onClick={copySnippet}
                                            className="absolute top-3 right-3 p-2 rounded-lg bg-gray-800 hover:bg-purple-900/40 text-gray-400 hover:text-purple-400 border border-gray-700 transition-all"
                                            title="Copiar código">
                                            {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
                                        </button>
                                    </div>
                                ) : (
                                    <div className="bg-gray-50 dark:bg-[#0b0e14] border border-gray-100 dark:border-[#374151] rounded-xl p-6 text-center text-gray-400 dark:text-gray-500 text-sm">
                                        Selecione um agente para gerar o código.
                                    </div>
                                )}

                                <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-800/30 rounded-lg p-4">
                                    <p className="text-xs text-blue-700 dark:text-blue-300 font-semibold mb-1">💡 Como funciona</p>
                                    <p className="text-xs text-blue-600/70 dark:text-blue-200/70">O widget aparece como um botão flutuante no canto do seu site. Os visitantes podem conversar com o agente diretamente, sem sair da página.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
