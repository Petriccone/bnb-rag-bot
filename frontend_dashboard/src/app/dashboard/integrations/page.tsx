"use client";

import React, { useState, useEffect } from 'react';
import { useI18n } from '@/lib/i18n-context';
import { Smartphone, CheckCircle, XCircle, Loader2, MessageCircle, Send } from 'lucide-react';
import { apiClient } from '@/lib/api';

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

    const fetchStatuses = async () => {
        try {
            setLoading(true);

            // Fetch WhatsApp Status
            try {
                const waRes = await apiClient.get('/whatsapp/status');
                if (waRes.status === 200) {
                    const waData = waRes.data;
                    setWaStatus({ connected: waData.connected, message: waData.message || 'Desconectado' });
                }
            } catch (e) {
                console.error("WhatsApp status error", e);
            }

            // Fetch Telegram Status
            try {
                // Assuming a generic status route exists or we just handle errors
                const tgRes = await apiClient.get('/telegram/status');
                if (tgRes.status === 200) {
                    const tgData = tgRes.data;
                    setTgStatus({ connected: tgData.connected, message: tgData.message || 'Desconectado' });
                } else {
                    setTgStatus({ connected: false, message: 'Status não disponível' });
                }
            } catch (e) {
                console.error("Telegram status error", e);
                setTgStatus({ connected: false, message: 'Desconectado' });
            }

        } catch (error) {
            console.error('Error fetching integrations status:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatuses();
    }, []);

    const handleConnectWhatsApp = async () => {
        // Simple placeholder for connection start, depends on exact implementation (QR code, Evolution API, Cloud API)
        alert('Instruções de conexão do WhatsApp devem ser seguidas conforme a documentação da API (Evolution API ou Meta Cloud).');
    };

    const handleDisconnectWhatsApp = async () => {
        try {
            setWaLoading(true);
            await apiClient.delete('/whatsapp/disconnect');
            fetchStatuses();
        } catch (e) {
            console.error(e);
        } finally {
            setWaLoading(false);
        }
    };

    const handleConnectTelegram = async () => {
        if (!tgToken) {
            alert("Informe o token do Bot do Telegram.");
            return;
        }
        try {
            setTgLoading(true);
            const formData = new FormData();
            // Create a text file containing the token
            const blob = new Blob([tgToken], { type: 'text/plain' });
            formData.append('token_file', blob, 'token.txt');

            const response = await apiClient.post('/telegram/connect-with-file', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            if (response.status === 200 || response.status === 201) {
                alert("Telegram conectado com sucesso!");
                setTgToken('');
                fetchStatuses();
            } else {
                alert("Erro ao conectar Telegram.");
            }
        } catch (e) {
            console.error(e);
            alert("Erro ao conectar Telegram.");
        } finally {
            setTgLoading(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white">Integrações</h1>
                    <p className="text-gray-400">Conecte seus agentes aos canais de comunicação.</p>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center items-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* WhatsApp Card */}
                    <div className="bg-[#111827] p-6 shadow rounded-xl border border-[#1f2937] flex flex-col">
                        <div className="flex items-center mb-4">
                            <div className="w-12 h-12 bg-green-900/30 rounded-lg flex items-center justify-center mr-4">
                                <MessageCircle className="h-6 w-6 text-green-400" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-white">WhatsApp</h2>
                                <p className="text-sm text-gray-400">Integração oficial Meta ou Evolution API</p>
                            </div>
                        </div>

                        <div className="bg-[#0b0e14] border border-[#1f2937] p-4 rounded-lg mb-6 flex-1">
                            <div className="flex items-center mb-2">
                                <span className="text-sm font-semibold text-gray-400 w-24">Status:</span>
                                {waStatus.connected ? (
                                    <span className="flex items-center text-green-400 text-sm font-medium">
                                        <CheckCircle className="h-4 w-4 mr-1" /> Conectado
                                    </span>
                                ) : (
                                    <span className="flex items-center text-gray-400 text-sm font-medium">
                                        <XCircle className="h-4 w-4 mr-1" /> Desconectado
                                    </span>
                                )}
                            </div>
                            <div className="flex items-start">
                                <span className="text-sm font-semibold text-gray-400 w-24 mt-0.5">Detalhes:</span>
                                <span className="text-sm text-gray-300 flex-1">{waStatus.message}</span>
                            </div>
                        </div>

                        <div className="flex justify-end mt-auto">
                            {waStatus.connected ? (
                                <button
                                    onClick={handleDisconnectWhatsApp}
                                    disabled={waLoading}
                                    className="px-4 py-2 border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition text-sm font-medium disabled:opacity-50"
                                >
                                    {waLoading ? 'Desconectando...' : 'Desconectar'}
                                </button>
                            ) : (
                                <button
                                    onClick={handleConnectWhatsApp}
                                    disabled={waLoading}
                                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center text-sm font-bold disabled:opacity-50"
                                >
                                    Conectar WhatsApp
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Telegram Card */}
                    <div className="bg-[#111827] p-6 shadow rounded-xl border border-[#1f2937] flex flex-col">
                        <div className="flex items-center mb-4">
                            <div className="w-12 h-12 bg-blue-900/30 rounded-lg flex items-center justify-center mr-4">
                                <Send className="h-6 w-6 text-blue-400" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-white">Telegram</h2>
                                <p className="text-sm text-gray-400">Bot oficial do Telegram</p>
                            </div>
                        </div>

                        <div className="bg-[#0b0e14] border border-[#1f2937] p-4 rounded-lg mb-6 flex-1">
                            <div className="flex items-center mb-2">
                                <span className="text-sm font-semibold text-gray-400 w-24">Status:</span>
                                {tgStatus.connected ? (
                                    <span className="flex items-center text-green-400 text-sm font-medium">
                                        <CheckCircle className="h-4 w-4 mr-1" /> Conectado
                                    </span>
                                ) : (
                                    <span className="flex items-center text-gray-400 text-sm font-medium">
                                        <XCircle className="h-4 w-4 mr-1" /> Desconectado
                                    </span>
                                )}
                            </div>
                            <div className="flex items-start">
                                <span className="text-sm font-semibold text-gray-400 w-24 mt-0.5">Detalhes:</span>
                                <span className="text-sm text-gray-300 flex-1">{tgStatus.message}</span>
                            </div>
                        </div>

                        <div className="flex flex-col gap-3 mt-auto">
                            {!tgStatus.connected && (
                                <input
                                    type="text"
                                    placeholder="Cole o token do Bot (BotFather) aqui"
                                    value={tgToken}
                                    onChange={(e) => setTgToken(e.target.value)}
                                    className="w-full text-sm text-white bg-[#0b0e14] border-[#374151] rounded-lg px-3 py-2 border focus:ring-[#8b5cf6] focus:border-[#8b5cf6] placeholder-gray-500"
                                />
                            )}
                            <div className="flex justify-end">
                                {tgStatus.connected ? (
                                    <button
                                        className="px-4 py-2 border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition text-sm font-medium opacity-50 cursor-not-allowed"
                                        title="Para desconectar, limpe o token no BotFather."
                                    >
                                        Conectado
                                    </button>
                                ) : (
                                    <button
                                        onClick={handleConnectTelegram}
                                        disabled={tgLoading || !tgToken}
                                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center text-sm font-bold disabled:opacity-50"
                                    >
                                        {tgLoading ? 'Conectando...' : 'Conectar Telegram'}
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
