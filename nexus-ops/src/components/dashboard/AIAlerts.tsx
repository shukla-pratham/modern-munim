import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { GlassCard } from '@/components/shared/GlassCard';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { RadialProgress } from '@/components/shared/RadialProgress';
import { aiAlerts } from '@/data/mockDashboard';

const riskColorMap: Record<string, string> = {
  critical: 'hsl(var(--destructive))',
  high: 'hsl(var(--orange))',
  medium: 'hsl(var(--cyan))',
  low: 'hsl(var(--emerald))',
};

export function AIAlerts() {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="text-base font-semibold text-foreground">AI Alerts</h2>
        <span className="text-xs bg-magenta/15 text-magenta px-2 py-0.5 rounded-full font-medium">
          {aiAlerts.length} active
        </span>
      </div>

      <motion.div
        className="space-y-3"
        initial="hidden"
        animate="show"
        variants={{ show: { transition: { staggerChildren: 0.08 } } }}
      >
        {aiAlerts.map((alert) => (
          <motion.div
            key={alert.id}
            variants={{
              hidden: { opacity: 0, y: 12, scale: 0.98 },
              show: { opacity: 1, y: 0, scale: 1 },
            }}
            transition={{ duration: 0.35 }}
          >
            <GlassCard
              hover={false}
              className="relative overflow-hidden border-magenta/20 p-4"
            >
              {/* Magenta glow edge */}
              <div className="absolute inset-y-0 left-0 w-[2px] bg-gradient-to-b from-magenta/60 via-magenta to-magenta/60 animate-pulse-glow" />

              <div className="flex items-start gap-4">
                <RadialProgress
                  value={alert.confidence}
                  size={44}
                  strokeWidth={3.5}
                  color={riskColorMap[alert.riskLevel]}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <StatusBadge level={alert.riskLevel} />
                    <span className="text-xs text-muted-foreground">{alert.timestamp}</span>
                  </div>
                  <p className="text-sm font-medium text-foreground leading-snug">{alert.title}</p>

                  <button
                    onClick={() => setExpanded(expanded === alert.id ? null : alert.id)}
                    className="flex items-center gap-1 mt-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <span>Why?</span>
                    <motion.div
                      animate={{ rotate: expanded === alert.id ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDown className="h-3 w-3" />
                    </motion.div>
                  </button>

                  <AnimatePresence>
                    {expanded === alert.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: 'easeInOut' }}
                        className="overflow-hidden"
                      >
                        <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                          <p>{alert.explanation}</p>
                          <div className="p-2.5 rounded-lg bg-primary/5 border border-primary/10">
                            <p className="font-medium text-foreground mb-0.5">Recommended Action</p>
                            <p>{alert.recommendation}</p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
