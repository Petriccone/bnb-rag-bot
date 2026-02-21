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
                className="flex items-center gap-1 p-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-[#1f2937] rounded-lg transition"
                aria-label="Change language"
            >
                <Globe className="h-4 w-4" />
                <span className="hidden sm:inline text-xs">{localeFlags[locale]}</span>
                <span className="sm:hidden text-xs">{localeFlags[locale]}</span>
            </button>

            {open && (
                <div className="absolute right-0 mt-1 w-36 bg-white dark:bg-[#1f2937] border border-gray-200 dark:border-[#374151] rounded-lg shadow-lg z-[9999] overflow-hidden">
                    {locales.map((loc) => (
                        <button
                            key={loc}
                            onClick={() => { setLocale(loc); setOpen(false); }}
                            className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm hover:bg-gray-50 dark:hover:bg-[#374151] transition ${locale === loc ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 font-medium' : 'text-gray-700 dark:text-gray-300'
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
