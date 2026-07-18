import { cn } from '@/lib/utils';
import { RiskLevel } from '@/data/types';

interface StatusBadgeProps {
  level: RiskLevel;
  className?: string;
}

const levelConfig: Record<RiskLevel, { label: string; classes: string }> = {
  low: { label: 'Low Risk', classes: 'bg-emerald/15 text-emerald border-emerald/30' },
  medium: { label: 'Medium', classes: 'bg-cyan/15 text-cyan border-cyan/30' },
  high: { label: 'High Risk', classes: 'bg-orange/15 text-orange border-orange/30' },
  critical: { label: 'Critical', classes: 'bg-destructive/15 text-destructive border-destructive/30' },
};

export function StatusBadge({ level, className }: StatusBadgeProps) {
  const config = levelConfig[level];
  return (
    <span className={cn(
      'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold',
      config.classes,
      className
    )}>
      {config.label}
    </span>
  );
}
