import { cn } from '@/lib/utils';
import { GlassCard } from './GlassCard';

interface ChartWrapperProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  className?: string;
}

export function ChartWrapper({ title, subtitle, children, className }: ChartWrapperProps) {
  return (
    <GlassCard hover={false} className={cn('p-5', className)}>
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
      </div>
      <div className="w-full h-[220px]">
        {children}
      </div>
    </GlassCard>
  );
}
