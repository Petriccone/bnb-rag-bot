"use client";

import { I18nProvider } from '@/lib/i18n-context';
import { ThemeProvider } from 'next-themes';

export default function ClientProviders({ children }: { children: React.ReactNode }) {
    return (
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} forcedTheme={undefined}>
            <I18nProvider>
                {children}
            </I18nProvider>
        </ThemeProvider>
    );
}
