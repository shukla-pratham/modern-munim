import { useState, useEffect, Suspense, lazy } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppSettings } from '@/contexts/SettingsContext';

const IntroScene = lazy(() => import('./IntroScene'));

export default function CinematicIntro({ onComplete }: { onComplete: () => void }) {
  const { shouldAnimate } = useAppSettings();
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 400),
      setTimeout(() => setPhase(2), 1200),
      setTimeout(() => setPhase(3), 2000),
      setTimeout(() => setPhase(4), 3000),
      setTimeout(() => onComplete(), 4500),
    ];
    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #0B1120 0%, #0f172a 50%, #0B1120 100%)' }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.8 }}
      >
        {/* Gradient overlay */}
        <motion.div
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(ellipse at 50% 40%, rgba(37, 99, 235, 0.08) 0%, transparent 70%)',
          }}
          animate={{ opacity: [0.3, 0.7, 0.3] }}
          transition={{ duration: 4, repeat: Infinity }}
        />

        {/* 3D Ring */}
        {shouldAnimate && (
          <div className="absolute inset-0 opacity-30">
            <Suspense fallback={null}>
              <IntroScene />
            </Suspense>
          </div>
        )}

        {/* Logo */}
        <div className="relative z-10 flex flex-col items-center gap-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={phase >= 1 ? { opacity: 1, scale: 1 } : {}}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="flex items-center gap-3"
          >
            <div className="relative">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center font-bold text-xl" style={{ color: 'white' }}>
                MM
              </div>
              <motion.div
                className="absolute inset-0 rounded-xl"
                style={{ boxShadow: '0 0 30px rgba(37, 99, 235, 0.4)' }}
                animate={{ opacity: [0.4, 0.8, 0.4] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </div>
            <span className="text-3xl font-bold tracking-tight" style={{ color: '#e2e8f0' }}>
              Modern Munim
            </span>
          </motion.div>

          {/* Animated line */}
          <motion.div
            className="h-px w-0"
            style={{ background: 'linear-gradient(90deg, transparent, #2563EB, transparent)' }}
            animate={phase >= 2 ? { width: 200 } : {}}
            transition={{ duration: 0.6, ease: 'easeInOut' }}
          />

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={phase >= 3 ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6 }}
            className="text-sm font-medium tracking-[0.3em] uppercase"
            style={{ color: '#64748b' }}
          >
           Your One Stop Shop for all your business needs
          </motion.p>
        </div>

        {/* Skip */}
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          whileHover={{ opacity: 1 }}
          onClick={onComplete}
          className="absolute top-6 right-6 text-sm font-medium px-3 py-1.5 rounded-md transition-colors"
          style={{ color: '#64748b', border: '1px solid rgba(100,116,139,0.3)' }}
        >
          Skip Intro
        </motion.button>
      </motion.div>
    </AnimatePresence>
  );
}
