"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useI18n } from '@/lib/i18n-context';
import { Locale, localeNames, localeFlags } from '@/lib/i18n';
import { Globe } from 'lucide-react';

export default function LanguageSelector() {
    const { locale, setLocale } = useI18n();
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const locales: Locale[] = ['pt', 'en', 'es'];

    return (
        <div className="relative" ref={ref}>
            <button
                onClick={() => setOpen(!open)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition"
                aria-label="Change language"
            >
                <Globe className="h-4 w-4" />
                <span>{localeFlags[locale]}</span>
            </button>

            {open && (
                <div className="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden">
                    {locales.map((loc) => (
                        <button
                            key={loc}
                            onClick={() => { setLocale(loc); setOpen(false); }}
                            className={`w-full flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-50 transition ${locale === loc ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                                }`}
                        >
                            <span>{localeFlags[loc]}</span>
                            <span>{localeNames[loc]}</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
