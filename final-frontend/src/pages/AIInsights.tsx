import { Suspense, lazy } from 'react';
import { motion } from 'framer-motion';
import { Brain, TrendingUp, AlertTriangle, ShoppingCart, BarChart3 } from 'lucide-react';
import { useAppSettings } from '@/contexts/SettingsContext';

const IntroScene = lazy(() => import('@/components/IntroScene'));

const insights = [
  {
    icon: TrendingUp,
    title: 'Demand Forecasting',
    description: 'AI predicts 23% surge in hydraulic pump demand next quarter based on seasonal patterns and market signals.',
    confidence: 91,
    impact: 'High',
  },
  {
    icon: AlertTriangle,
    title: 'Vendor Risk Alert',
    description: 'Parker Hannifin shows declining delivery scores. Risk of supply disruption within 60 days.',
    confidence: 78,
    impact: 'Critical',
  },
  {
    icon: BarChart3,
    title: 'Price Volatility',
    description: 'Steel bearing prices expected to increase 8-12% due to raw material shortages. Consider forward contracts.',
    confidence: 85,
    impact: 'Medium',
  },
  {
    icon: ShoppingCart,
    title: 'Autonomous PO Suggestion',
    description: 'Auto-reorder recommended for 5 critical SKUs below safety stock. Estimated savings: $12,400.',
    confidence: 94,
    impact: 'High',
  },
];

function ConfidenceGauge({ value }: { value: number }) {
  const circumference = 2 * Math.PI * 70;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <div className="relative w-48 h-48 mx-auto">
      <svg viewBox="0 0 160 160" className="w-full h-full -rotate-90">
        <circle cx="80" cy="80" r="70" fill="none" stroke="hsl(var(--border))" strokeWidth="8" />
        <motion.circle
          cx="80" cy="80" r="70"
          fill="none"
          stroke="hsl(var(--ai))"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-foreground">{value}%</span>
        <span className="text-xs text-muted-foreground">AI Confidence</span>
      </div>
    </div>
  );
}

export default function AIInsights() {
  const { shouldAnimate } = useAppSettings();
  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-6">
      {/* Hero section with 3D */}
      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-6 card-shadow relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row items-center gap-8">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-ai" />
              <h3 className="font-semibold text-foreground">AI Intelligence Engine</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Machine learning models analyze procurement patterns, vendor behavior, and market signals to deliver actionable predictions.
            </p>
            <div className="flex flex-wrap gap-2">
              {['Predictive Analytics', 'Risk Modeling', 'Auto-Optimization'].map(tag => (
                <span key={tag} className="text-xs px-2 py-1 bg-ai/10 text-ai rounded-md border border-ai/20">{tag}</span>
              ))}
            </div>
          </div>
          <div className="relative">
            <ConfidenceGauge value={87} />
            {shouldAnimate && (
              <div className="absolute inset-0 opacity-20 pointer-events-none" style={{ width: 200, height: 200, left: -4, top: -4 }}>
                <Suspense fallback={null}>
                  <IntroScene />
                </Suspense>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, i) => (
          <motion.div
            key={i}
            variants={fadeUp}
            className="bg-card border border-border rounded-xl p-5 card-shadow hover:card-shadow-hover transition-shadow group"
          >
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-ai/10 flex items-center justify-center flex-shrink-0">
                <insight.icon className="w-4 h-4 text-ai" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-semibold text-foreground">{insight.title}</h4>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
                    insight.impact === 'Critical' ? 'bg-critical/10 text-critical border-critical/20' :
                    insight.impact === 'High' ? 'bg-warning/10 text-warning border-warning/20' :
                    'bg-data/10 text-data border-data/20'
                  }`}>{insight.impact}</span>
                </div>
                <p className="text-xs text-muted-foreground mb-3">{insight.description}</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-secondary rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${insight.confidence}%` }}
                      transition={{ duration: 1, delay: i * 0.2 }}
                      className="h-full bg-ai rounded-full"
                    />
                  </div>
                  <span className="text-xs text-muted-foreground">{insight.confidence}%</span>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
