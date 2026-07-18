import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Brain, Package, DollarSign, Users, ShieldAlert } from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  salesTrendData, quarterlyData, inventoryMovementData, expenseBreakdownData,
  vendorPerformanceData,
} from '@/data/mockData';

function AnimatedNumber({ value, prefix = '', suffix = '' }: { value: number; prefix?: string; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<number>();

  useEffect(() => {
    const start = 0;
    const duration = 1200;
    const startTime = performance.now();
    const animate = (now: number) => {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.floor(start + (value - start) * eased));
      if (progress < 1) ref.current = requestAnimationFrame(animate);
    };
    ref.current = requestAnimationFrame(animate);
    return () => { if (ref.current) cancelAnimationFrame(ref.current); };
  }, [value]);

  return <span>{prefix}{display.toLocaleString()}{suffix}</span>;
}

const kpis = [
  { title: 'Inventory Health', value: 87, suffix: '%', icon: Package, color: 'text-success', bgColor: 'bg-success/10', trend: '+2.3%', up: true },
  { title: 'Monthly Expenses', value: 284500, prefix: '$', icon: DollarSign, color: 'text-warning', bgColor: 'bg-warning/10', trend: '-4.1% vs budget', up: false },
  { title: 'Vendor Reliability', value: 92, suffix: '%', icon: Users, color: 'text-primary', bgColor: 'bg-primary/10', trend: '+1.8%', up: true },
  { title: 'Stockout Risk', value: 7, suffix: ' SKUs', icon: ShieldAlert, color: 'text-critical', bgColor: 'bg-critical/10', trend: '+3 this week', up: true },
  { title: 'AI Alerts', value: 12, icon: Brain, color: 'text-ai', bgColor: 'bg-ai/10', trend: '3 critical', up: false },
];

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState<'monthly' | 'quarterly'>('monthly');
  const [selectedExpense, setSelectedExpense] = useState<string | null>(null);
  const [activeVendors, setActiveVendors] = useState<Set<string>>(new Set(vendorPerformanceData.map(v => v.name)));
  const chartData = timeRange === 'monthly' ? salesTrendData : quarterlyData;
  const xKey = timeRange === 'monthly' ? 'month' : 'quarter';

  const toggleVendor = (name: string) => {
    setActiveVendors(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
  };

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {kpis.map(kpi => (
          <motion.div
            key={kpi.title}
            variants={fadeUp}
            className="bg-card border border-border rounded-xl p-4 card-shadow hover:card-shadow-hover transition-shadow cursor-pointer group"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`w-9 h-9 rounded-lg ${kpi.bgColor} flex items-center justify-center`}>
                <kpi.icon className={`w-4 h-4 ${kpi.color}`} />
              </div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                {kpi.up ? <TrendingUp className="w-3 h-3 text-success" /> : <TrendingDown className="w-3 h-3 text-warning" />}
                {kpi.trend}
              </div>
            </div>
            <p className="text-2xl font-bold text-foreground">
              <AnimatedNumber value={kpi.value} prefix={kpi.prefix} suffix={kpi.suffix} />
            </p>
            <p className="text-xs text-muted-foreground mt-1">{kpi.title}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Trend */}
        <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-foreground text-sm">Sales Trend</h3>
            <div className="flex gap-1 bg-secondary rounded-lg p-0.5">
              {(['monthly', 'quarterly'] as const).map(t => (
                <button
                  key={t}
                  onClick={() => setTimeRange(t)}
                  className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${timeRange === t ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="salesGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey={xKey} tick={{ fontSize: 11, fill: 'white' }} />
              <YAxis tick={{ fontSize: 11, fill: 'white' }} />
              <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: 12 }} />
              <Area type="monotone" dataKey="sales" stroke="hsl(var(--primary))" fill="url(#salesGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Inventory Movement */}
        <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
          <h3 className="font-semibold text-foreground text-sm mb-4">Inventory Movement</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={inventoryMovementData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'white' }} />
              <YAxis tick={{ fontSize: 11, fill: 'white' }} />
              <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: 12 }} />
              <Bar dataKey="inbound" fill="hsl(var(--success))" radius={[4, 4, 0, 0]} />
              <Bar dataKey="outbound" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              <Bar dataKey="returns" fill="hsl(var(--warning))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Expense Breakdown */}
        <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
          <h3 className="font-semibold text-foreground text-sm mb-4">Expense Breakdown</h3>
          <div className="flex items-center gap-4">
            <ResponsiveContainer width="50%" height={200}>
              <PieChart>
                <Pie
                  data={expenseBreakdownData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                  onClick={(d) => setSelectedExpense(d.name === selectedExpense ? null : d.name)}
                >
                  {expenseBreakdownData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.color}
                      opacity={!selectedExpense || entry.name === selectedExpense ? 1 : 0.3}
                      cursor="pointer"
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: 'hsl(var(--primary))',
                    border: '1px solid hsl(var(--primary))',
                    borderRadius: '8px',
                    fontSize: 12,
                    color: '#fff',
                  }}
                  itemStyle={{ color: '#fff' }}
                  labelStyle={{ color: '#87CEEB' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {expenseBreakdownData.map(item => (
                <div
                  key={item.name}
                  onClick={() => setSelectedExpense(item.name === selectedExpense ? null : item.name)}
                  className={`flex items-center justify-between text-xs cursor-pointer px-2 py-1 rounded transition-opacity ${selectedExpense && selectedExpense !== item.name ? 'opacity-40' : 'opacity-100'}`}
                >
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ background: item.color }} />
                    <span className="text-muted-foreground">{item.name}</span>
                  </div>
                  <span className="text-foreground font-medium">${(item.value / 1000).toFixed(0)}k</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Vendor Performance */}
        <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
          <h3 className="font-semibold text-foreground text-sm mb-4">Vendor Performance</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'white' }} allowDuplicatedCategory={false} />
              <YAxis domain={[50, 100]} tick={{ fontSize: 11, fill: 'white' }} />
              <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: 12 }} />
              {vendorPerformanceData.map((vendor, i) => (
                activeVendors.has(vendor.name) && (
                  <Line
                    key={vendor.name}
                    data={vendor.data}
                    dataKey="score"
                    name={vendor.name}
                    stroke={`hsl(var(--chart-${(i % 5) + 1}))`}
                    strokeWidth={2}
                    dot={false}
                  />
                )
              ))}
            </LineChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-3">
            {vendorPerformanceData.map((v, i) => (
              <button
                key={v.name}
                onClick={() => toggleVendor(v.name)}
                className={`text-xs px-2 py-1 rounded-md border transition-all ${activeVendors.has(v.name) ? 'border-border bg-secondary text-foreground' : 'border-transparent text-muted-foreground opacity-50'}`}
              >
                <span className="inline-block w-2 h-2 rounded-full mr-1" style={{ background: `hsl(var(--chart-${(i % 5) + 1}))` }} />
                {v.name.split(' ')[0]}
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
