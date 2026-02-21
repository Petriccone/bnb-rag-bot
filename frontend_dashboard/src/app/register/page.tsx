"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useI18n } from '@/lib/i18n-context';
import LanguageSelector from '@/components/LanguageSelector';
import Link from 'next/link';

export default function RegisterPage() {
    const router = useRouter();
    const { t } = useI18n();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await apiClient.post('/auth/register', {
                email,
                password,
                name,
                company_name: `${name}'s Company`
            });

            const res = await apiClient.post('/auth/login', {
                email,
                password
            });

            localStorage.setItem('access_token', res.data.access_token);
            if (res.data.tenants && res.data.tenants.length > 0) {
                localStorage.setItem('tenant_id', res.data.tenants[0].id);
            }
            router.push('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Falha no cadastro. Tente outro e-mail.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0b0e14] to-[#1e1b4b] flex flex-col items-center pt-4 px-4 sm:px-6 lg:px-8">
            <div className="absolute top-2 right-2 sm:top-4 sm:right-4 z-20 text-white">
                <LanguageSelector />
            </div>

            <div className="w-full max-w-md">
                {/* Logo - 16px from top, 16px to heading */}
                <div className="flex justify-center mb-4">
                    <img src="/botfy-logo.png" alt="Botfy" className="h-[140px] w-auto drop-shadow-[0_0_15px_rgba(139,92,246,0.3)]" />
                </div>
                <h2 className="text-center text-2xl sm:text-3xl font-extrabold text-white">
                    {t.signUpTitle}
                </h2>
                <p className="mt-1 text-center text-sm text-gray-400">
                    {t.alreadyHaveAccount}{' '}
                    <Link href="/login" className="font-semibold text-[#8b5cf6] hover:text-[#7c3aed]">
                        {t.signIn}
                    </Link>
                </p>

                <div className="mt-4 w-full">
                    <div className="bg-[#111827] py-8 px-4 shadow-2xl rounded-2xl sm:px-10 border border-[#1f2937]">
                        <form className="space-y-5" onSubmit={handleSubmit}>
                            {error && (
                                <div className="bg-red-50 border-l-4 border-red-400 p-3 rounded">
                                    <p className="text-sm text-red-700">{error}</p>
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-gray-300">{t.fullName}</label>
                                <input type="text" required value={name} onChange={e => setName(e.target.value)}
                                    className="mt-1 block text-white bg-[#0b0e14] font-medium w-full px-3 py-2.5 border border-[#374151] rounded-lg shadow-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-[#8b5cf6] sm:text-sm" />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300">{t.email}</label>
                                <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                                    className="mt-1 block text-white bg-[#0b0e14] font-medium w-full px-3 py-2.5 border border-[#374151] rounded-lg shadow-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-[#8b5cf6] sm:text-sm" />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300">{t.password}</label>
                                <input type="password" required value={password} onChange={e => setPassword(e.target.value)}
                                    className="mt-1 block text-white bg-[#0b0e14] font-medium w-full px-3 py-2.5 border border-[#374151] rounded-lg shadow-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-[#8b5cf6] sm:text-sm" />
                            </div>

                            <button type="submit" disabled={loading}
                                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-[#8b5cf6] hover:bg-[#7c3aed] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#8b5cf6] focus:ring-offset-[#111827] disabled:opacity-50 transition">
                                {loading ? t.signingUp : t.signUpCta}
                            </button>
                        </form>

                        {/* Divider */}
                        <div className="relative mt-6 mb-6">
                            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-[#374151]" /></div>
                            <div className="relative flex justify-center text-sm"><span className="px-3 bg-[#111827] text-gray-500">{t.orContinueWith}</span></div>
                        </div>

                        {/* Social Login */}
                        <div className="space-y-3">
                            <button type="button" onClick={() => alert(t.oauthPending)} className="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-[#374151] rounded-lg shadow-sm text-sm font-medium text-gray-300 bg-[#0b0e14] hover:bg-[#1f2937] transition">
                                <svg className="h-5 w-5" viewBox="0 0 24 24">
                                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                                </svg>
                                {t.continueWithGoogle}
                            </button>
                            <button type="button" onClick={() => alert(t.oauthPending)} className="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-[#374151] rounded-lg shadow-sm text-sm font-medium text-gray-300 bg-[#0b0e14] hover:bg-[#1f2937] transition">
                                <svg className="h-5 w-5 text-gray-200" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.32 2.32-2.12 4.45-3.74 4.25z" />
                                </svg>
                                {t.continueWithApple}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
