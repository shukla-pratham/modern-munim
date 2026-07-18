import { createContext, useContext, type ReactNode } from 'react';
import { useSettings, type AppSettings } from '@/hooks/useSettings';

interface SettingsContextType {
  settings: AppSettings;
  updateSettings: (updates: Partial<AppSettings>) => void;
  resetData: () => void;
  shouldAnimate: boolean;
  motionDuration: number;
}

const SettingsContext = createContext<SettingsContextType | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const value = useSettings();
  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useAppSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useAppSettings must be used within SettingsProvider');
  return ctx;
}
