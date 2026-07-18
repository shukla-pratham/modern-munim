import { cn } from '@/lib/utils';
import { motion, type HTMLMotionProps } from 'framer-motion';
import React from 'react';

interface GlassCardProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
  children: React.ReactNode;
  className?: string;
  glowColor?: 'primary' | 'cyan' | 'magenta' | 'orange';
  hover?: boolean;
}

export function GlassCard({ children, className, glowColor, hover = true, ...props }: GlassCardProps) {
  const glowClasses: Record<string, string> = {
    primary: 'glow-primary',
    cyan: 'glow-cyan',
    magenta: 'glow-magenta',
    orange: 'glow-orange',
  };

  return (
    <motion.div
      className={cn(
        'glass rounded-2xl p-6',
        glowColor && glowClasses[glowColor],
        className
      )}
      whileHover={hover ? { y: -2, scale: 1.01 } : undefined}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      {...props}
    >
      {children}
    </motion.div>
  );
}
