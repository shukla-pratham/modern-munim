import type {
  DashboardExpenseBreakdownResponse,
  DashboardSalesOverTime,
} from '@/lib/api';

/** FastAPI/Spring default window. Do not invent a custom date-range UI. */
export const DASHBOARD_DAYS = 30;

export const EXPENSE_CATEGORY_ORDER = ['inventory', 'operations', 'marketing', 'salary', 'miscellaneous'] as const;

export const EXPENSE_CATEGORY_COLORS: Record<(typeof EXPENSE_CATEGORY_ORDER)[number], string> = {
  inventory: 'hsl(var(--primary))',
  operations: 'hsl(var(--warning))',
  marketing: 'hsl(var(--ai))',
  salary: 'hsl(var(--success, 142 76% 45%))',
  miscellaneous: 'hsl(var(--muted-foreground, 215 20% 65%))',
};

export function toNumber(value: number | string | null | undefined): number {
  if (value == null || value === '') return 0;
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : 0;
}

export function categoryLabel(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function periodLabel(period: string | null | undefined): string {
  if (!period) return `Last ${DASHBOARD_DAYS} days`;
  const match = /^last_(\d+)_days$/.exec(period);
  if (match) return `Last ${match[1]} days`;
  return period;
}

export interface ExpensePieSlice {
  name: string;
  key: string;
  value: number;
  color: string;
}

/** Uses only the three FastAPI/Spring category keys. Does not invent mock categories. */
export function expensePieData(
  byCategory: DashboardExpenseBreakdownResponse['by_category'] | null | undefined
): ExpensePieSlice[] {
  const src = byCategory ?? {};
  return EXPENSE_CATEGORY_ORDER.map((key) => ({
    name: categoryLabel(key),
    key,
    value: toNumber(src[key]),
    color: EXPENSE_CATEGORY_COLORS[key],
  }));
}

export interface SalesTrendPoint {
  date: string;
  orders: number;
  sales: number;
}

export function salesTrendPoints(
  rows: DashboardSalesOverTime[] | null | undefined
): SalesTrendPoint[] {
  return (rows ?? []).map((row) => ({
    date: row.date,
    orders: toNumber(row.orders),
    sales: toNumber(row.revenue),
  }));
}

export function apiErrorMessage(err: unknown, fallback: string): string {
  const ax = err as {
    response?: { data?: { detail?: unknown; error?: string }; status?: number };
    message?: string;
  };
  const detail = ax.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (ax.response?.status === 403) return 'Not enough permissions';
  if (ax.response?.status === 401) return 'Could not validate credentials';
  if (!ax.response) return 'Could not reach the dashboard API';
  return ax.message || fallback;
}
