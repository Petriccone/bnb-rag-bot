"use client";

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { useI18n } from '@/lib/i18n-context';
import { Check } from 'lucide-react';

export default function BillingPage() {
    const { t } = useI18n();
    const [loading, setLoading] = useState(false);
    const [currentPlan, setCurrentPlan] = useState('free');

    useEffect(() => {
        const tenant_id = localStorage.getItem('tenant_id');
        apiClient.get('/usage', { headers: { 'x-tenant-id': tenant_id } })
            .then(res => setCurrentPlan(res.data?.plan || 'free'))
            .catch(() => { });
    }, []);

    const handleCheckout = async (priceId: string) => {
        setLoading(true);
        try {
            const tenant_id = localStorage.getItem('tenant_id');
            const res = await apiClient.post('/billing/create-checkout-session', { price_id: priceId }, { headers: { 'x-tenant-id': tenant_id } });
            if (res.data?.url) window.location.href = res.data.url;
        } catch { alert("Falha ao criar sessão de checkout."); setLoading(false); }
    };

    const handleCustomerPortal = async () => {
        setLoading(true);
        try {
            const tenant_id = localStorage.getItem('tenant_id');
            const res = await apiClient.post('/billing/customer-portal', {}, { headers: { 'x-tenant-id': tenant_id } });
            if (res.data?.url) window.location.href = res.data.url;
        } catch { alert("Portal indisponível."); setLoading(false); }
    };

    const tiers = [
        {
            name: 'Starter',
            price: '€49',
            description: { pt: 'Perfeito para testes e pequenos projetos.', en: 'Perfect for testing and small projects.', es: 'Perfecto para pruebas y pequeños proyectos.' },
            features: {
                pt: ['1 Agente de IA', '500 Mensagens/mês', 'Web Widget', 'Suporte da Comunidade'],
                en: ['1 AI Agent', '500 Messages/mo', 'Web Widget', 'Community Support'],
                es: ['1 Agente de IA', '500 Mensajes/mes', 'Web Widget', 'Soporte de la Comunidad']
            },
            paymentLink: 'https://buy.stripe.com/fZu4gB3WGaEF8exdYSfQI00',
        },
        {
            name: 'Growth',
            price: '€149',
            description: { pt: 'Para equipes em crescimento.', en: 'For growing teams scaling AI operations.', es: 'Para equipos en crecimiento.' },
            features: {
                pt: ['5 Agentes de IA', '5.000 Mensagens/mês', 'Integração WhatsApp', 'Suporte Prioritário'],
                en: ['5 AI Agents', '5,000 Messages/mo', 'WhatsApp Integration', 'Priority Support'],
                es: ['5 Agentes de IA', '5.000 Mensajes/mes', 'Integración WhatsApp', 'Soporte Prioritario']
            },
            paymentLink: 'https://buy.stripe.com/aFabJ32SCdQR7atg70fQI01',
        },
        {
            name: 'Business',
            price: '€499',
            description: { pt: 'Controles avançados para maiores organizações.', en: 'Advanced controls for larger organizations.', es: 'Controles avanzados para organizaciones más grandes.' },
            features: {
                pt: ['Agentes Ilimitados', '50.000 Mensagens/mês', 'Integrações Customizadas', 'Gerente de Conta Dedicado'],
                en: ['Unlimited Agents', '50,000 Messages/mo', 'Custom Integrations', 'Dedicated Account Manager'],
                es: ['Agentes Ilimitados', '50.000 Mensajes/mes', 'Integraciones Personalizadas', 'Gerente de Cuenta Dedicado']
            },
            paymentLink: 'https://buy.stripe.com/eVqfZj78S3cd1Q9aMGfQI02',
        },
        {
            name: 'Enterprise',
            price: { pt: 'Sob Consulta', en: 'Custom', es: 'A Consultar' },
            description: { pt: 'Para empresas necessitando de segurança máxima.', en: 'For companies needing maximum security.', es: 'Para empresas que necesitan de seguridad máxima.' },
            features: {
                pt: ['Volume Personalizado', 'Opções On-Premise', 'SLA Personalizado', 'Auditorias de Segurança'],
                en: ['Custom Volume', 'On-Premise Options', 'Custom SLA', 'Security Audits'],
                es: ['Volumen Personalizado', 'Opciones On-Premise', 'SLA Personalizado', 'Auditorias de Seguridad']
            },
            paymentLink: 'contact_sales',
        },
    ];

    return (
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
            <div className="text-center">
                <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white transition-colors duration-200">{t.billingTitle || 'Planos'}</h1>
                <p className="mt-4 text-xl text-gray-600 dark:text-gray-400 transition-colors duration-200">{t.billingSubtitle || 'Start building for free, upgrade when you need more power and volume.'}</p>
            </div>

            {currentPlan !== 'free' && currentPlan !== 'starter' && (
                <div className="mt-8 flex justify-center">
                    <button onClick={handleCustomerPortal} disabled={loading}
                        className="px-6 py-2 border border-gray-200 dark:border-[#1f2937] shadow-sm text-base font-medium rounded-lg text-gray-700 dark:text-gray-300 bg-white dark:bg-[#111827] hover:bg-gray-50 dark:hover:bg-[#1f2937] transition transition-colors duration-200">
                        {t.manageSubscription}
                    </button>
                </div>
            )}

            <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 max-w-7xl mx-auto">
                {tiers.map((tier) => {
                    const desc = typeof tier.description === 'string' ? tier.description : (tier.description as any)[t.platformName === 'Botfy' ? 'pt' : 'en'];
                    const feats: string[] = (tier.features as any)['pt'];
                    const price = typeof tier.price === 'string' ? tier.price : (tier.price as any)['pt'];

                    // Use locale-aware values
                    const locale = localStorage?.getItem('botfy_locale') || 'pt';
                    const localizedDesc = (tier.description as any)[locale] || desc;
                    const localizedFeats: string[] = (tier.features as any)[locale] || feats;
                    const localizedPrice = typeof tier.price === 'string' ? tier.price : (tier.price as any)[locale] || price;

                    return (
                        <div key={tier.name} className={`flex flex-col border rounded-2xl shadow-sm bg-white dark:bg-[#111827] relative overflow-visible transition-all duration-300 ${currentPlan === tier.name.toLowerCase() ? 'ring-2 ring-blue-500 dark:ring-[#8b5cf6] border-blue-500 dark:border-[#8b5cf6]' : 'border-gray-200 dark:border-[#1f2937]'}`}>
                            {tier.name === 'Growth' && (
                                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-10">
                                    <span className="bg-blue-600 dark:bg-[#8b5cf6] text-white text-[10px] sm:text-xs font-bold px-4 py-1.5 rounded-full uppercase tracking-wider whitespace-nowrap shadow-lg ring-4 ring-white dark:ring-[#111827]">
                                        Most Popular
                                    </span>
                                </div>
                            )}
                            <div className={`p-6 flex flex-col flex-grow ${tier.name === 'Growth' ? 'pt-8' : ''}`}>
                                <h2 className="text-lg font-bold text-gray-900 dark:text-white transition-colors duration-200">{tier.name}</h2>
                                <p className="mt-3 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200 leading-relaxed h-10">{localizedDesc}</p>
                                <div className="mt-6">
                                    <span className="text-4xl font-extrabold text-gray-900 dark:text-white transition-colors duration-200">{localizedPrice}</span>
                                    {!['Sob Consulta', 'Custom', 'A Consultar'].includes(localizedPrice) && <span className="text-base font-medium text-gray-500 ml-1">{t.perMonth}</span>}
                                </div>
                                <div className="mt-auto pt-6">
                                    <button disabled={loading || tier.name.toLowerCase() === currentPlan}
                                        onClick={() => tier.paymentLink && !tier.paymentLink.startsWith('contact_sales') ? window.location.href = tier.paymentLink : undefined}
                                        className={`block w-full py-3 rounded-xl text-center text-sm font-bold transition-all duration-200 shadow-sm ${tier.name.toLowerCase() === currentPlan ? 'bg-gray-100 dark:bg-[#1f2937] text-gray-400 dark:text-gray-500 cursor-not-allowed border border-gray-200 dark:border-[#374151]'
                                            : 'bg-blue-600 dark:bg-[#8b5cf6] text-white hover:bg-blue-700 dark:hover:bg-[#7c3aed] hover:shadow-md active:scale-[0.98]'
                                            }`}>
                                        {tier.name.toLowerCase() === currentPlan ? t.currentPlan : tier.paymentLink?.startsWith('contact_sales') ? 'Contact Sales' : `${t.subscribeTo || 'Get Started'}`}
                                    </button>
                                </div>
                            </div>
                            <div className="pt-6 pb-8 px-6 border-t border-gray-200 dark:border-[#1f2937] transition-colors duration-200">
                                <h3 className="text-xs font-medium text-gray-500 tracking-wide uppercase">{t.whatsIncluded || 'What\'s Included'}</h3>
                                <ul className="mt-4 space-y-3">
                                    {localizedFeats.map((feature: string) => (
                                        <li key={feature} className="flex items-start gap-2">
                                            <Check className="flex-shrink-0 h-5 w-5 text-blue-500 dark:text-[#8b5cf6] mt-0.5 transition-colors duration-200" />
                                            <span className="text-sm text-gray-700 dark:text-gray-300 transition-colors duration-200">{feature}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
