"use client";

import React, { useState, useEffect } from 'react';
import { useI18n } from '@/lib/i18n-context';
import { Settings, Save, Building, Bell, Shield, Smartphone } from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function SettingsPage() {
    const { t } = useI18n();
    const [companyName, setCompanyName] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        // Fetch current settings
    }, []);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            // Save settings logic
            setTimeout(() => {
                setLoading(false);
                setSuccess(true);
                setTimeout(() => setSuccess(false), 3000);
            }, 1000);
        } catch (err) {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-900 mb-8">{t.navSettings || 'Configurações'}</h1>

            <div className="space-y-6">
                <form onSubmit={handleSave} className="bg-white shadow rounded-xl border border-gray-200 overflow-hidden">
                    <div className="p-6 border-b border-gray-100">
                        <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                            <Building className="h-5 w-5 mr-3 text-blue-600" />
                            Perfil da Empresa
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">Informações básicas da sua conta corporativa.</p>
                    </div>

                    <div className="p-6 space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Nome da Empresa</label>
                            <input
                                type="text"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                placeholder="Botfy AI Solutions"
                                className="w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 py-2 px-3 border"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">E-mail de Contato</label>
                            <input
                                type="email"
                                placeholder="contato@empresa.com"
                                className="w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 py-2 px-3 border"
                            />
                        </div>
                    </div>

                    <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-end">
                        <button
                            type="submit"
                            disabled={loading}
                            className="bg-blue-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-blue-700 transition disabled:bg-blue-300 flex items-center shadow-sm"
                        >
                            <Save className="h-4 w-4 mr-2" />
                            {loading ? 'Salvando...' : 'Salvar Alterações'}
                        </button>
                    </div>
                </form>

                {success && (
                    <div className="fixed bottom-8 right-8 bg-green-600 text-white px-6 py-3 rounded-xl shadow-2xl animate-bounce">
                        Configurações salvas com sucesso!
                    </div>
                )}
            </div>
        </div>
    );
}
