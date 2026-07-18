import { GlassCard } from './GlassCard';
import { AnimatedNumber } from './AnimatedNumber';
import { cn } from '@/lib/utils';
import { Activity, DollarSign, Shield, AlertTriangle, Brain } from 'lucide-react';
import { KPIData } from '@/data/types';

const iconMap: Record<string, React.ElementType> = {
  Activity, DollarSign, Shield, AlertTriangle, Brain,
};

const accentMap: Record<string, string> = {
  primary: 'text-primary',
  cyan: 'text-cyan',
  orange: 'text-orange',
  magenta: 'text-magenta',
  emerald: 'text-emerald',
  destructive: 'text-destructive',
};

const bgAccentMap: Record<string, string> = {
  primary: 'bg-primary/10',
  cyan: 'bg-cyan/10',
  orange: 'bg-orange/10',
  magenta: 'bg-magenta/10',
  emerald: 'bg-emerald/10',
  destructive: 'bg-destructive/10',
};

interface StatCardProps {
  data: KPIData;
  index: number;
}

export function StatCard({ data, index }: StatCardProps) {
  const Icon = iconMap[data.icon] || Activity;
  const isAI = data.accentColor === 'magenta';

  return (
    <GlassCard
      className={cn(
        'relative overflow-hidden',
        isAI && 'border-magenta/30 animate-pulse-glow'
      )}
      glowColor={isAI ? 'magenta' : undefined}
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.06, duration: 0.4, ease: 'easeOut' }}
    >
      {isAI && (
        <div className="absolute inset-0 bg-gradient-to-r from-magenta/5 to-transparent pointer-events-none" />
      )}
      <div className="flex items-start justify-between mb-3">
        <div className={cn('p-2 rounded-lg', bgAccentMap[data.accentColor])}>
          <Icon className={cn('h-5 w-5', accentMap[data.accentColor])} />
        </div>
        <span className="text-xs text-muted-foreground">{data.updatedAgo}</span>
      </div>
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground font-medium">{data.label}</p>
        <AnimatedNumber
          value={data.value}
          prefix={data.prefix}
          suffix={data.suffix}
          className="text-2xl font-bold tracking-tight"
          decimals={data.value % 1 !== 0 ? 1 : 0}
        />
        <div className="flex items-center gap-1.5 mt-1">
          <span className={cn(
            'text-xs font-medium',
            data.trend > 0 ? 'text-emerald' : 'text-orange'
          )}>
            {data.trend > 0 ? '↑' : '↓'} {Math.abs(data.trend)}%
          </span>
          <span className="text-xs text-muted-foreground">{data.trendLabel}</span>
        </div>
      </div>
    </GlassCard>
  );
}
