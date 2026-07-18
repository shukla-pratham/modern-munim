import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Package,
  Users,
  FileText,
  Receipt,
  Brain,
  ChevronLeft,
  Zap,
} from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

const navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, active: true },
  { label: 'Inventory', path: '/inventory', icon: Package, comingSoon: true },
  { label: 'Vendors', path: '/vendors', icon: Users, active: true },
  { label: 'Purchase Orders', path: '/purchase-orders', icon: FileText, comingSoon: true },
  { label: 'Expenses', path: '/expenses', icon: Receipt, comingSoon: true },
  { label: 'AI Insights', path: '/ai-insights', icon: Brain, comingSoon: true },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <motion.aside
      className="h-screen sticky top-0 flex flex-col border-r border-border bg-sidebar noise-bg z-30"
      animate={{ width: collapsed ? 64 : 240 }}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-sidebar-border">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
            <Zap className="h-4 w-4 text-primary-foreground" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="font-bold text-sm whitespace-nowrap text-sidebar-foreground"
              >
                FF Marketplace
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-hidden">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;

          const button = (
            <motion.button
              key={item.path}
              onClick={() => !item.comingSoon && navigate(item.path)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors relative',
                isActive
                  ? 'bg-sidebar-accent text-sidebar-primary'
                  : item.comingSoon
                  ? 'text-muted-foreground/50 cursor-default'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-primary'
              )}
              whileHover={!item.comingSoon ? { x: 2 } : undefined}
              whileTap={!item.comingSoon ? { scale: 0.97 } : undefined}
            >
              {isActive && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-primary rounded-r-full"
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
              <Icon className="h-4.5 w-4.5 flex-shrink-0" />
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="whitespace-nowrap flex-1 text-left"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
              {!collapsed && item.comingSoon && (
                <span className="text-[10px] bg-muted/60 text-muted-foreground px-1.5 py-0.5 rounded-full">
                  Soon
                </span>
              )}
            </motion.button>
          );

          if (collapsed) {
            return (
              <Tooltip key={item.path}>
                <TooltipTrigger asChild>{button}</TooltipTrigger>
                <TooltipContent side="right" className="glass-strong">
                  <p>{item.label}</p>
                  {item.comingSoon && <p className="text-xs text-muted-foreground">Coming Soon</p>}
                </TooltipContent>
              </Tooltip>
            );
          }

          return button;
        })}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-2 border-t border-sidebar-border">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-sidebar-accent/60 text-muted-foreground transition-colors"
        >
          <motion.div
            animate={{ rotate: collapsed ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronLeft className="h-4 w-4" />
          </motion.div>
        </button>
      </div>
    </motion.aside>
  );
}
