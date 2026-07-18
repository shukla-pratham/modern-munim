import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowUpDown, X } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { GlassCard } from '@/components/shared/GlassCard';
import { AnimatedNumber } from '@/components/shared/AnimatedNumber';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Input } from '@/components/ui/input';
import { vendors } from '@/data/mockVendors';
import { Vendor, RiskLevel } from '@/data/types';
import {
  LineChart, Line, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  BarChart, Bar, XAxis, YAxis, Tooltip,
} from 'recharts';

const scoreColor = (score: number) => {
  if (score >= 90) return 'text-emerald';
  if (score >= 75) return 'text-cyan';
  if (score >= 60) return 'text-orange';
  return 'text-destructive';
};

const scoreBg = (score: number) => {
  if (score >= 90) return 'bg-emerald/10';
  if (score >= 75) return 'bg-cyan/10';
  if (score >= 60) return 'bg-orange/10';
  return 'bg-destructive/10';
};

const riskFilters: RiskLevel[] = ['low', 'medium', 'high', 'critical'];

function VendorCard({ vendor, rank, selected, onSelect }: { vendor: Vendor; rank: number; selected: boolean; onSelect: () => void }) {
  const isTop = rank === 1;

  return (
    <motion.div
      whileHover={{ y: -4, rotateX: 2, rotateY: -1 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      style={{ perspective: 800 }}
    >
      <GlassCard
        hover={false}
        onClick={onSelect}
        className={`cursor-pointer relative overflow-hidden ${
          selected ? 'border-primary ring-1 ring-primary/30' : ''
        } ${isTop ? 'border-emerald/40' : ''}`}
      >
        {isTop && (
          <div className="absolute -top-1 -right-1 w-20 h-20 bg-gradient-to-bl from-emerald/20 to-transparent rounded-bl-full" />
        )}

        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${isTop ? 'bg-emerald/15 text-emerald animate-pulse-glow' : 'bg-muted text-muted-foreground'}`}>
                #{rank}
              </span>
              <StatusBadge level={vendor.riskLevel} />
            </div>
            <h3 className="text-sm font-semibold text-foreground mt-2">{vendor.name}</h3>
            <p className="text-xs text-muted-foreground">{vendor.category}</p>
          </div>
          <div className={`text-right p-2.5 rounded-xl ${scoreBg(vendor.overallScore)}`}>
            <AnimatedNumber value={vendor.overallScore} className={`text-2xl font-bold ${scoreColor(vendor.overallScore)}`} />
          </div>
        </div>

        {/* Sub-scores */}
        <div className="space-y-2 mb-3">
          {[
            { label: 'Reliability', value: vendor.reliabilityScore },
            { label: 'Cost', value: vendor.costScore },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground w-16">{label}</span>
              <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                <motion.div
                  className={`h-full rounded-full ${value >= 90 ? 'bg-emerald' : value >= 75 ? 'bg-cyan' : 'bg-orange'}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${value}%` }}
                  transition={{ duration: 0.8, delay: 0.3, ease: 'easeOut' }}
                />
              </div>
              <span className="text-xs font-medium w-7 text-right">{value}</span>
            </div>
          ))}
        </div>

        {/* Sparkline */}
        <div className="h-10 mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={vendor.scoreHistory}>
              <Line type="monotone" dataKey="score" stroke="hsl(188,95%,43%)" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
          <span>Lead: {vendor.leadTimeDays}d</span>
          <span>OTD: {vendor.onTimeDeliveryRate}%</span>
        </div>
      </GlassCard>
    </motion.div>
  );
}

function ComparisonPanel({ vendors: selectedVendors, onClose }: { vendors: Vendor[]; onClose: () => void }) {
  const [a, b] = selectedVendors;
  const dimensions = ['reliabilityScore', 'costScore', 'qualityScore', 'deliveryScore', 'communicationScore'] as const;
  const radarData = dimensions.map((d) => ({
    metric: d.replace('Score', '').replace(/([A-Z])/g, ' $1').trim(),
    [a.name]: a[d],
    [b.name]: b[d],
  }));

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-end justify-center bg-background/40 backdrop-blur-sm"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="w-full max-w-4xl glass-strong rounded-t-2xl p-6 max-h-[80vh] overflow-auto"
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">Vendor Comparison</h2>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-accent transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Score comparison bars */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-muted-foreground">Score Comparison</h3>
            {dimensions.map((d) => {
              const label = d.replace('Score', '').replace(/([A-Z])/g, ' $1').trim();
              return (
                <div key={d} className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="capitalize">{label}</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs w-8 text-right">{a[d]}</span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <motion.div className="h-full bg-primary rounded-full" initial={{ width: 0 }} animate={{ width: `${a[d]}%` }} transition={{ duration: 0.6 }} />
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs w-8 text-right">{b[d]}</span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <motion.div className="h-full bg-cyan rounded-full" initial={{ width: 0 }} animate={{ width: `${b[d]}%` }} transition={{ duration: 0.6, delay: 0.1 }} />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
            <div className="flex gap-4 text-xs mt-2">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 bg-primary rounded-full" />{a.name}</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 bg-cyan rounded-full" />{b.name}</span>
            </div>
          </div>

          {/* Radar chart */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Performance Radar</h3>
            <div className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="hsl(222,30%,25%)" />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fill: 'hsl(215,20%,65%)' }} />
                  <Radar name={a.name} dataKey={a.name} stroke="hsl(217,91%,53%)" fill="hsl(217,91%,53%)" fillOpacity={0.15} strokeWidth={2} />
                  <Radar name={b.name} dataKey={b.name} stroke="hsl(188,95%,43%)" fill="hsl(188,95%,43%)" fillOpacity={0.15} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Bottom metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          {[a, b].map((v) => (
            <GlassCard key={v.id} hover={false} className="p-3 text-center">
              <p className="text-xs text-muted-foreground mb-1">{v.name}</p>
              <p className="text-lg font-bold">{v.onTimeDeliveryRate}%</p>
              <p className="text-xs text-muted-foreground">On-Time Delivery</p>
            </GlassCard>
          ))}
          {[a, b].map((v) => (
            <GlassCard key={`pv-${v.id}`} hover={false} className="p-3 text-center">
              <p className="text-xs text-muted-foreground mb-1">{v.name}</p>
              <p className="text-lg font-bold">{v.priceVolatility}%</p>
              <p className="text-xs text-muted-foreground">Price Volatility</p>
            </GlassCard>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function VendorIntelligence() {
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'score' | 'name' | 'risk'>('score');
  const [riskFilter, setRiskFilter] = useState<RiskLevel[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const filtered = useMemo(() => {
    let result = vendors.filter((v) =>
      v.name.toLowerCase().includes(search.toLowerCase()) ||
      v.category.toLowerCase().includes(search.toLowerCase())
    );
    if (riskFilter.length > 0) {
      result = result.filter((v) => riskFilter.includes(v.riskLevel));
    }
    result.sort((a, b) => {
      if (sortBy === 'score') return b.overallScore - a.overallScore;
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      const riskOrder = { low: 0, medium: 1, high: 2, critical: 3 };
      return riskOrder[b.riskLevel] - riskOrder[a.riskLevel];
    });
    return result;
  }, [search, sortBy, riskFilter]);

  const sortedAll = [...vendors].sort((a, b) => b.overallScore - a.overallScore);
  const rankMap = Object.fromEntries(sortedAll.map((v, i) => [v.id, i + 1]));

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 2 ? [...prev, id] : [prev[1], id]
    );
  };

  const selectedVendors = selectedIds.map((id) => vendors.find((v) => v.id === id)!).filter(Boolean);

  return (
    <MainLayout title="Vendor Intelligence">
      <div className="max-w-[1400px] mx-auto space-y-6">
        {/* Search & Filters */}
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search vendors..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 h-10 bg-card/60 border-border/50"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setSortBy(sortBy === 'score' ? 'name' : sortBy === 'name' ? 'risk' : 'score')}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg glass hover:bg-accent/60 transition-colors"
            >
              <ArrowUpDown className="h-3.5 w-3.5" />
              Sort: {sortBy === 'score' ? 'Score' : sortBy === 'name' ? 'Name' : 'Risk'}
            </button>

            {riskFilters.map((level) => (
              <motion.button
                key={level}
                onClick={() => setRiskFilter((prev) =>
                  prev.includes(level) ? prev.filter((x) => x !== level) : [...prev, level]
                )}
                className={`px-2.5 py-1 text-xs rounded-full border transition-colors capitalize ${
                  riskFilter.includes(level)
                    ? 'bg-primary/15 border-primary/40 text-primary'
                    : 'border-border/50 text-muted-foreground hover:border-border'
                }`}
                whileTap={{ scale: 0.95 }}
                layout
              >
                {level}
              </motion.button>
            ))}
          </div>
        </div>

        {selectedIds.length > 0 && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Select {2 - selectedIds.length} more vendor{selectedIds.length === 0 ? 's' : ''} to compare</span>
            {selectedIds.length === 2 && (
              <span className="text-primary font-medium">Comparison ready — click below</span>
            )}
            <button onClick={() => setSelectedIds([])} className="ml-auto text-xs text-muted-foreground hover:text-foreground">
              Clear
            </button>
          </div>
        )}

        {/* Grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          layout
        >
          <AnimatePresence mode="popLayout">
            {filtered.map((vendor) => (
              <motion.div
                key={vendor.id}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.25 }}
              >
                <VendorCard
                  vendor={vendor}
                  rank={rankMap[vendor.id]}
                  selected={selectedIds.includes(vendor.id)}
                  onSelect={() => toggleSelect(vendor.id)}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>

        {/* Comparison */}
        <AnimatePresence>
          {selectedVendors.length === 2 && (
            <ComparisonPanel vendors={selectedVendors} onClose={() => setSelectedIds([])} />
          )}
        </AnimatePresence>
      </div>
    </MainLayout>
  );
}
