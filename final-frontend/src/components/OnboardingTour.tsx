import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Package,
  Building2,
  FileText,
  DollarSign,
  Brain,
  Settings,
  ArrowRight,
  CheckCircle2,
  X,
  Compass,
  Sparkles,
} from 'lucide-react';

interface TourStep {
  title: string;
  subtitle: string;
  description: string;
  icon: React.ElementType;
  badge: string;
  details: string[];
}

const tourSteps: TourStep[] = [
  {
    title: 'Welcome to Modern Munim',
    subtitle: 'Your B2B Operations Command Center',
    badge: 'Overview',
    icon: Compass,
    description:
      'Modern Munim unifies inventory tracking, supplier purchasing, expense management, and AI forecasting into a single high-performance dashboard.',
    details: [
      'Multi-tenant isolated workspaces for every store',
      'Real-time financial and inventory ledger sync',
      'AI-driven stockout prediction and dead-stock detection',
    ],
  },
  {
    title: 'Dashboard & Financials',
    subtitle: 'Revenue, Profit Margins, and Cashflow',
    badge: 'Dashboard',
    icon: LayoutDashboard,
    description:
      'Monitor net revenue, profit breakdown by SKU, and cost category distribution with interactive visual charts.',
    details: [
      'Daily and monthly revenue timelines',
      'Expense categorisation (Inventory, Operations, Marketing)',
      'Profit margin analysis per product',
    ],
  },
  {
    title: 'Inventory & Stock Ledger',
    subtitle: 'Complete SKU Lifecycle Control',
    badge: 'Inventory',
    icon: Package,
    description:
      'Manage catalog items, track stock quantities, configure minimum threshold alarms, and record stock-in/stock-out movements.',
    details: [
      'Double-entry inventory ledger transactions',
      'Automated low-stock threshold alerts',
      'Live stock status updates upon order delivery',
    ],
  },
  {
    title: 'Vendors & Intelligence',
    subtitle: 'Supplier Scorecards & Procurement',
    badge: 'Vendors',
    icon: Building2,
    description:
      'Maintain vendor contact directories, catalogue vendor-supplied items, and review automated vendor reliability scorecards.',
    details: [
      'Track lead times, on-time delivery rates, and quality grades',
      'Vendor-specific catalog pricing and minimum order quantities',
      'Direct purchase order creation from vendor profiles',
    ],
  },
  {
    title: 'Purchase Orders & Receiving',
    subtitle: 'Seamless Restocking Workflows',
    badge: 'Purchase Orders',
    icon: FileText,
    description:
      'Issue procurement orders to suppliers. When delivered, purchase orders automatically update on-hand stock and post inventory expenses.',
    details: [
      'Single-click delivery receipt and inventory increment',
      'Automatic expense recording in the ledger',
      'Vendor delivery delay tracking for scoring',
    ],
  },
  {
    title: 'Expenses & Budgeting',
    subtitle: 'Business Cost Tracking',
    badge: 'Expenses',
    icon: DollarSign,
    description:
      'Track operational, inventory, and marketing expenditures. Filter expenses by date, category, or associated inventory product.',
    details: [
      'Category breakdown with interactive visual metrics',
      'Automated expense capture from purchase orders',
      'Clear, audit-ready financial ledger trail',
    ],
  },
  {
    title: 'AI Insights & Forecasts',
    subtitle: 'Predictive Inventory Intelligence',
    badge: 'AI Insights',
    icon: Brain,
    description:
      'Leverage machine-learning models to predict demand spikes, calculate days-until-stockout, and detect slow-moving dead stock before it costs you.',
    details: [
      '7-day and 30-day demand forecast curves',
      'Stockout prediction risk scores and actionable explanations',
      'Smart restocking recommendations based on sales velocity',
    ],
  },
  {
    title: 'Settings & Security',
    subtitle: 'Account Preferences & Data Control',
    badge: 'Settings',
    icon: Settings,
    description:
      'Customize UI themes, animation intensity, and chart layout density. Safely manage app data with verified OTP confirmation.',
    details: [
      'Dark & Light mode toggle',
      'Reduced motion & animation tuning',
      'Secure email OTP authentication for sensitive operations',
    ],
  },
];

const TOUR_STORAGE_KEY = 'mm_user_intro_tour_completed';

interface OnboardingTourProps {
  forceOpen?: boolean;
  onClose?: () => void;
}

export default function OnboardingTour({ forceOpen = false, onClose }: OnboardingTourProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    if (forceOpen) {
      setIsOpen(true);
      setCurrentStepIndex(0);
      return;
    }
    const completed = localStorage.getItem(TOUR_STORAGE_KEY);
    if (!completed) {
      // Delay slightly so the user enters the app first
      const timer = setTimeout(() => {
        setIsOpen(true);
        setCurrentStepIndex(0);
      }, 600);
      return () => clearTimeout(timer);
    }
  }, [forceOpen]);

  const handleFinish = () => {
    localStorage.setItem(TOUR_STORAGE_KEY, 'true');
    setIsOpen(false);
    if (onClose) onClose();
  };

  const handleNext = () => {
    if (currentStepIndex < tourSteps.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      handleFinish();
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  if (!isOpen) return null;

  const step = tourSteps[currentStepIndex];
  const Icon = step.icon;
  const isLast = currentStepIndex === tourSteps.length - 1;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-background/80 backdrop-blur-md"
          onClick={handleFinish}
        />

        {/* Modal Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 16 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 16 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          className="relative w-full max-w-xl max-h-[90vh] bg-card border border-border rounded-2xl shadow-2xl overflow-hidden z-10 flex flex-col my-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header Banner */}
          <div className="relative px-5 sm:px-6 pt-5 sm:pt-6 pb-4 border-b border-border bg-gradient-to-r from-primary/10 via-primary/5 to-transparent">

            <button
              onClick={handleFinish}
              className="absolute top-5 right-5 text-muted-foreground hover:text-foreground p-1 rounded-lg transition-colors"
              aria-label="Close Tour"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary text-primary-foreground">
                <Sparkles className="w-3 h-3" />
                {step.badge}
              </span>
              <span className="text-xs text-muted-foreground font-mono">
                Step {currentStepIndex + 1} of {tourSteps.length}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center text-primary shrink-0">
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-foreground leading-tight">{step.title}</h3>
                <p className="text-xs text-muted-foreground font-medium">{step.subtitle}</p>
              </div>
            </div>
          </div>

          {/* Content Body */}
          <div className="p-4 sm:p-6 space-y-4 flex-1 overflow-y-auto">
            <p className="text-xs sm:text-sm text-foreground/90 leading-relaxed">{step.description}</p>

            <div className="bg-secondary/40 border border-border/60 rounded-xl p-3 sm:p-4 space-y-2">
              <p className="text-[10px] sm:text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Key Highlights:
              </p>
              <ul className="space-y-1.5 sm:space-y-2">
                {step.details.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-foreground/80">
                    <CheckCircle2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary shrink-0 mt-0.5" />
                    <span className="leading-tight">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Footer Controls */}
          <div className="px-4 sm:px-6 py-3 sm:py-4 border-t border-border bg-card flex flex-wrap items-center justify-between gap-2.5">
            {/* Step Indicators */}
            <div className="flex items-center gap-1">
              {tourSteps.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentStepIndex(idx)}
                  className={`h-1.5 rounded-full transition-all ${
                    idx === currentStepIndex
                      ? 'w-5 sm:w-6 bg-primary'
                      : 'w-1.5 sm:w-2 bg-muted hover:bg-muted-foreground/40'
                  }`}
                  aria-label={`Go to step ${idx + 1}`}
                />
              ))}
            </div>

            <div className="flex items-center gap-1.5 sm:gap-2 ml-auto">
              {currentStepIndex > 0 && (
                <button
                  type="button"
                  onClick={handlePrev}
                  className="px-2.5 sm:px-3.5 py-1.5 sm:py-2 rounded-lg border border-border bg-card text-foreground text-xs font-medium hover:bg-accent transition-colors"
                >
                  Previous
                </button>
              )}
              <button
                type="button"
                onClick={handleFinish}
                className="px-2.5 sm:px-3.5 py-1.5 sm:py-2 text-xs text-muted-foreground hover:text-foreground font-medium transition-colors"
              >
                Skip
              </button>
              <button
                type="button"
                onClick={handleNext}
                className="inline-flex items-center gap-1 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors shadow-sm"
              >
                <span>{isLast ? 'Get Started' : 'Next'}</span>
                {!isLast && <ArrowRight className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

        </motion.div>
      </div>
    </AnimatePresence>
  );
}
