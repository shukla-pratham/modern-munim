import { Suspense, lazy } from 'react';
import { motion } from 'framer-motion';
import { Brain } from 'lucide-react';
import { useAppSettings } from '@/contexts/SettingsContext';

const IntroScene = lazy(() => import('@/components/IntroScene'));

export default function AIInsights() {
  const { shouldAnimate } = useAppSettings();
  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-6 card-shadow relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row items-center gap-8">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-ai" />
              <h3 className="font-semibold text-foreground">AI Intelligence Engine</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              Forecasts, stockout predictions, and restock suggestions are written by the backend batch job.
              This screen does not invent scores. Nothing is available until that job has run.
            </p>
          </div>
          {shouldAnimate && (
            <div className="relative w-48 h-48 opacity-30 pointer-events-none">
              <Suspense fallback={null}>
                <IntroScene />
              </Suspense>
            </div>
          )}
        </div>
      </motion.div>
      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-8 card-shadow text-center text-sm text-muted-foreground">
        No AI results yet.
      </motion.div>
    </motion.div>
  );
}
