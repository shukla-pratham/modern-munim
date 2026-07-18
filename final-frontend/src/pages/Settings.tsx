import { motion } from 'framer-motion';
import { Sun, Moon, Gauge, RotateCcw, Eye, BarChart3 } from 'lucide-react';
import { useAppSettings } from '@/contexts/SettingsContext';

export default function SettingsPage() {
  const { settings, updateSettings, resetData } = useAppSettings();

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="max-w-2xl space-y-6">
      {/* Theme */}
      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          {settings.theme === 'dark' ? <Moon className="w-5 h-5 text-primary" /> : <Sun className="w-5 h-5 text-primary" />}
          <h3 className="font-semibold text-foreground">Theme</h3>
        </div>
        <div className="flex gap-3">
          {(['dark', 'light'] as const).map(t => (
            <button
              key={t}
              onClick={() => updateSettings({ theme: t })}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-medium transition-all border ${
                settings.theme === t ? 'bg-primary text-primary-foreground border-primary' : 'bg-secondary text-muted-foreground border-border hover:text-foreground'
              }`}
            >
              {t === 'dark' ? '🌙 Dark' : '☀️ Light'}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Motion */}
      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          <Eye className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Reduced Motion</h3>
        </div>
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">Disable heavy animations and transitions</p>
          <button
            onClick={() => updateSettings({ reducedMotion: !settings.reducedMotion })}
            className={`relative w-12 h-6 rounded-full transition-colors ${settings.reducedMotion ? 'bg-primary' : 'bg-secondary'}`}
          >
            <motion.div
              animate={{ x: settings.reducedMotion ? 24 : 2 }}
              className="absolute top-1 w-4 h-4 bg-primary-foreground rounded-full shadow"
            />
          </button>
        </div>
      </motion.div>

      {/* Animation Intensity */}
      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          <Gauge className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Animation Intensity</h3>
        </div>
        <div className="flex gap-3">
          {(['minimal', 'balanced', 'expressive'] as const).map(level => (
            <button
              key={level}
              onClick={() => updateSettings({ animationIntensity: level })}
              className={`flex-1 px-3 py-2.5 rounded-lg text-sm font-medium transition-all border capitalize ${
                settings.animationIntensity === level ? 'bg-primary text-primary-foreground border-primary' : 'bg-secondary text-muted-foreground border-border hover:text-foreground'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Chart Density */}
      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Chart Density</h3>
        </div>
        <div className="flex gap-3">
          {(['compact', 'comfortable', 'spacious'] as const).map(d => (
            <button
              key={d}
              onClick={() => updateSettings({ chartDensity: d })}
              className={`flex-1 px-3 py-2.5 rounded-lg text-sm font-medium transition-all border capitalize ${
                settings.chartDensity === d ? 'bg-primary text-primary-foreground border-primary' : 'bg-secondary text-muted-foreground border-border hover:text-foreground'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Reset */}
      <motion.div variants={fadeUp}>
        <button
          onClick={resetData}
          className="flex items-center gap-2 px-4 py-2.5 bg-destructive text-destructive-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
        >
          <RotateCcw className="w-4 h-4" />
          Reset All Mock Data
        </button>
      </motion.div>
    </motion.div>
  );
}
