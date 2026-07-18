import { useState, useEffect, useCallback } from 'react';

export interface AppSettings {
  theme: 'dark' | 'light';
  reducedMotion: boolean;
  animationIntensity: 'minimal' | 'balanced' | 'expressive';
  chartDensity: 'compact' | 'comfortable' | 'spacious';
  introSeen: boolean;
}

const defaultSettings: AppSettings = {
  theme: 'dark',
  reducedMotion: false,
  animationIntensity: 'balanced',
  chartDensity: 'comfortable',
  introSeen: false,
};

function getStoredSettings(): AppSettings {
  try {
    const stored = localStorage.getItem('ff-settings');
    if (stored) return { ...defaultSettings, ...JSON.parse(stored) };
  } catch {}
  return defaultSettings;
}

export function useSettings() {
  const [settings, setSettingsState] = useState<AppSettings>(getStoredSettings);

  useEffect(() => {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) {
      setSettingsState(s => ({ ...s, reducedMotion: true }));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('ff-settings', JSON.stringify(settings));
    if (settings.theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [settings]);

  const updateSettings = useCallback((updates: Partial<AppSettings>) => {
    setSettingsState(s => ({ ...s, ...updates }));
  }, []);

  const resetData = useCallback(() => {
    localStorage.removeItem('ff-settings');
    localStorage.removeItem('ff-auth');
    setSettingsState({ ...defaultSettings, theme: settings.theme });
  }, [settings.theme]);

  const shouldAnimate = !settings.reducedMotion;
  const motionDuration = settings.animationIntensity === 'minimal' ? 0.15 : settings.animationIntensity === 'expressive' ? 0.4 : 0.25;

  return { settings, updateSettings, resetData, shouldAnimate, motionDuration };
}
