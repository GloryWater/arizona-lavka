import React, { useEffect } from 'react';
import { useThemeStore } from '@/features/theme/model/useThemeStore';

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: 'light' | 'dark';
}

export function ThemeProvider({ children, defaultTheme = 'dark' }: ThemeProviderProps) {
  const { theme, setTheme } = useThemeStore();

  useEffect(() => {
    if (!theme) {
      setTheme(defaultTheme);
    }
  }, [theme, setTheme, defaultTheme]);

  return <>{children}</>;
}
