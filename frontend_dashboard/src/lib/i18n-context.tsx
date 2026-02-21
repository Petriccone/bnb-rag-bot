"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Locale, Translations, translations } from './i18n';

interface I18nContextType {
    locale: Locale;
    t: Translations;
    setLocale: (locale: Locale) => void;
}

const I18nContext = createContext<I18nContextType>({
    locale: 'pt',
    t: translations.pt,
    setLocale: () => { },
});

export function I18nProvider({ children }: { children: ReactNode }) {
    const [locale, setLocaleState] = useState<Locale>('pt');

    useEffect(() => {
        const saved = localStorage.getItem('botfy_locale') as Locale | null;
        if (saved && translations[saved]) {
            setLocaleState(saved);
        }
    }, []);

    const setLocale = (newLocale: Locale) => {
        setLocaleState(newLocale);
        localStorage.setItem('botfy_locale', newLocale);
    };

    return (
        <I18nContext.Provider value={{ locale, t: translations[locale], setLocale }}>
            {children}
        </I18nContext.Provider>
    );
}

export function useI18n() {
    return useContext(I18nContext);
}
