"use client";

import React from 'react';
import { useI18n } from '@/lib/i18n-context';
import { Locale } from '@/lib/i18n';

const LANGS: { locale: Locale; label: string }[] = [
    { locale: 'en', label: 'EN' },
    { locale: 'pt', label: 'PT' },
    { locale: 'es', label: 'ES' },
];

export default function LanguageSelector() {
    const { locale, setLocale } = useI18n();

    return (
        <div className="flex items-center bg-gray-100 dark:bg-[#1f2937] rounded-full p-0.5 gap-0.5">
            {LANGS.map(({ locale: loc, label }) => (
                <button
                    key={loc}
                    onClick={() => setLocale(loc)}
                    className={`
                        px-2.5 py-1 rounded-full text-xs font-semibold transition-all duration-200
                        ${locale === loc
                            ? 'bg-[#1f2937] dark:bg-[#374151] text-white shadow-sm'
                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                        }
                    `}
                    aria-label={`Switch to ${label}`}
                >
                    {label}
                </button>
            ))}
        </div>
    );
}
