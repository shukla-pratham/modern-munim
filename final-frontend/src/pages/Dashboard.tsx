import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, DollarSign, ShieldAlert, Loader2, ChevronRight } from 'lucide-react';
import {
  AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  dashboardAPI,
  type DashboardExpenseBreakdownResponse,
  type DashboardProfitResponse,
  type DashboardRevenueResponse,
  type DashboardSalesResponse,
  type DashboardStockStatusResponse,
} from '@/lib/api';
import {
  DASHBOARD_DAYS,
  apiErrorMessage,
  expensePieData,
  periodLabel,
  salesTrendPoints,
  toNumber,
} from '@/lib/dashboardDisplay';

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

function formatMoney(value: number): string {
  return `₹${toNumber(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

type DashLink = {
  title: string;
  value: number;
  prefix?: string;
  suffix?: string;
  icon: typeof DollarSign;
  color: string;
  bgColor: string;
  trend: string;
  up: boolean;
  to: string;
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revenue, setRevenue] = useState<DashboardRevenueResponse | null>(null);
  const [expenses, setExpenses] = useState<DashboardExpenseBreakdownResponse | null>(null);
  const [profit, setProfit] = useState<DashboardProfitResponse | null>(null);
  const [stock, setStock] = useState<DashboardStockStatusResponse | null>(null);
  const [sales, setSales] = useState<DashboardSalesResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      dashboardAPI.revenue(DASHBOARD_DAYS),
      dashboardAPI.expenses(DASHBOARD_DAYS),
      dashboardAPI.profit(DASHBOARD_DAYS),
      dashboardAPI.stockStatus(),
      dashboardAPI.sales(DASHBOARD_DAYS),
    ])
      .then(([revRes, expRes, profitRes, stockRes, salesRes]) => {
        if (cancelled) return;
        setRevenue(revRes.data);
        setExpenses(expRes.data);
        setProfit(profitRes.data);
        setStock(stockRes.data);
        setSales(salesRes.data);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(apiErrorMessage(err, 'Failed to load dashboard'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl border border-destructive/20 bg-destructive/10 text-destructive text-sm">
        {error}
      </div>
    );
  }

  const period = periodLabel(revenue?.period);
  const pieData = expensePieData(expenses?.by_category);
  const trendData = salesTrendPoints(sales?.sales_over_time);
  const totalExpenses = toNumber(expenses?.total_expenses);
  const netProfit = toNumber(profit?.net_profit);
  const outOfStock = stock?.out_of_stock_products?.length ?? 0;
  const lowStock = stock?.low_stock_products?.length ?? 0;
  const atRiskSkus = outOfStock + lowStock;
  const pieHasValue = pieData.some((s) => s.value > 0);

  const kpis: DashLink[] = [
    {
      title: 'Monthly Expenses',
      value: totalExpenses,
      prefix: '₹',
      icon: DollarSign,
      color: 'text-warning',
      bgColor: 'bg-warning/10',
      trend: period,
      up: false,
      to: '/expenses',
    },
    {
      title: 'Stockout Risk',
      value: atRiskSkus,
      suffix: ' SKUs',
      icon: ShieldAlert,
      color: 'text-critical',
      bgColor: 'bg-critical/10',
      trend: `${outOfStock} out · ${lowStock} low`,
      up: atRiskSkus > 0,
      to: '/inventory',
    },
  ];

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {kpis.map((kpi) => (
          <motion.button
            key={kpi.title}
            type="button"
            variants={fadeUp}
            onClick={() => navigate(kpi.to)}
            className="bg-card border border-border rounded-xl p-4 card-shadow hover:card-shadow-hover hover:border-primary/40 transition-all group text-left cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`w-9 h-9 rounded-lg ${kpi.bgColor} flex items-center justify-center`}>
                <kpi.icon className={`w-4 h-4 ${kpi.color}`} />
              </div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                {kpi.up ? <TrendingUp className="w-3 h-3 text-success" /> : <TrendingDown className="w-3 h-3 text-warning" />}
                {kpi.trend}
                <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
            <p className="text-2xl font-bold text-foreground">
              <AnimatedNumber value={kpi.value} prefix={kpi.prefix} suffix={kpi.suffix} />
            </p>
            <p className="text-xs text-muted-foreground mt-1">{kpi.title}</p>
          </motion.button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.button
          type="button"
          variants={fadeUp}
          onClick={() => navigate('/purchase-orders')}
          className="bg-card border border-border rounded-xl p-5 card-shadow hover:card-shadow-hover hover:border-primary/40 transition-all text-left cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary group"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-foreground text-sm flex items-center gap-1">
              Sales Trend
              <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
            </h3>
            <span className="text-xs text-muted-foreground">
              {formatMoney(toNumber(sales?.total_revenue ?? revenue?.total_revenue))} · {period}
            </span>
          </div>
          {trendData.length === 0 ? (
            <div className="h-[240px] flex items-center justify-center text-sm text-muted-foreground">
              No completed sales in the last {DASHBOARD_DAYS} days — open purchase orders
            </div>
          ) : (
            <div className="pointer-events-none">
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="salesGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'white' }} />
                  <YAxis tick={{ fontSize: 11, fill: 'white' }} />
                  <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: 12 }} />
                  <Area type="monotone" dataKey="sales" stroke="hsl(var(--primary))" fill="url(#salesGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </motion.button>

        <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
          <button
            type="button"
            onClick={() => navigate('/expenses')}
            className="w-full flex items-center justify-between mb-4 text-left cursor-pointer group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded"
          >
            <h3 className="font-semibold text-foreground text-sm flex items-center gap-1">
              Expense Breakdown
              <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
            </h3>
            <span className="text-xs text-muted-foreground">
              Net {formatMoney(netProfit)}
            </span>
          </button>
          {!pieHasValue ? (
            <button
              type="button"
              onClick={() => navigate('/expenses')}
              className="h-[200px] w-full flex items-center justify-center text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            >
              No expenses in the last {DASHBOARD_DAYS} days — open expenses
            </button>
          ) : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="50%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                    onClick={(d) => {
                      const payload = d as { key?: string; payload?: { key?: string } };
                      const key = payload.key ?? payload.payload?.key;
                      navigate(key ? `/expenses?category=${key}` : '/expenses');
                    }}
                  >
                    {pieData.map((entry) => (
                      <Cell
                        key={entry.key}
                        fill={entry.color}
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
                {pieData.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => navigate(`/expenses?category=${item.key}`)}
                    className="flex items-center justify-between text-xs w-full cursor-pointer px-2 py-1 rounded hover:bg-accent transition-colors text-left"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: item.color }} />
                      <span className="text-muted-foreground">{item.name}</span>
                    </div>
                    <span className="text-foreground font-medium">{formatMoney(item.value)}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}
