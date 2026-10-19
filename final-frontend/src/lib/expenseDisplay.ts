import type { ExpenseCreate, ExpenseResponse, ExpenseUpdate } from '@/lib/api';
import {
  EXPENSE_CATEGORY_COLORS,
  EXPENSE_CATEGORY_ORDER,
  categoryLabel,
  toNumber,
} from '@/lib/dashboardDisplay';

export { EXPENSE_CATEGORY_ORDER, categoryLabel, toNumber };

export const EXPENSE_TYPE_ORDER = ['one_time', 'recurring'] as const;

export type ExpenseFormFields = {
  category: string;
  description: string;
  amount: string;
  expenseType: string;
  productId: string;
};

function parseOptionalProductId(raw: string): { ok: true; value?: number } | { ok: false; error: string } {
  const trimmed = raw.trim();
  if (!trimmed) return { ok: true };
  const n = Number(trimmed);
  if (!Number.isInteger(n) || n <= 0) return { ok: false, error: 'Product ID must be a positive integer' };
  return { ok: true, value: n };
}

export function buildExpenseCreatePayload(
  fields: ExpenseFormFields,
): { ok: true; body: ExpenseCreate } | { ok: false; error: string } {
  const category = fields.category.trim();
  const description = fields.description.trim();
  const expenseType = fields.expenseType.trim();
  if (!category) return { ok: false, error: 'Category is required' };
  if (!description) return { ok: false, error: 'Description is required' };
  const amount = Number(fields.amount);
  if (!Number.isFinite(amount) || amount < 0) return { ok: false, error: 'Valid amount required' };
  if (!expenseType) return { ok: false, error: 'Expense type is required' };
  const product = parseOptionalProductId(fields.productId);
  if (!product.ok) return product;
  return {
    ok: true,
    body: {
      category,
      description,
      amount,
      expense_type: expenseType,
      ...(product.value != null ? { product_id: product.value } : {}),
    },
  };
}

export function buildExpenseUpdatePayload(
  fields: ExpenseFormFields,
): { ok: true; body: ExpenseUpdate } | { ok: false; error: string } {
  const created = buildExpenseCreatePayload(fields);
  if (!created.ok) return created;
  return {
    ok: true,
    body: {
      category: created.body.category,
      description: created.body.description,
      amount: created.body.amount,
      expense_type: created.body.expense_type,
      ...(created.body.product_id != null ? { product_id: created.body.product_id } : {}),
    },
  };
}

export interface CategorySpend {
  key: (typeof EXPENSE_CATEGORY_ORDER)[number];
  name: string;
  actual: number;
  count: number;
  color: string;
}

export function totalsByCategory(expenses: ExpenseResponse[] | null | undefined): CategorySpend[] {
  const rows = expenses ?? [];
  return EXPENSE_CATEGORY_ORDER.map((key) => {
    const matching = rows.filter((e) => e.category === key);
    return {
      key,
      name: categoryLabel(key),
      actual: matching.reduce((sum, e) => sum + toNumber(e.amount), 0),
      count: matching.length,
      color: EXPENSE_CATEGORY_COLORS[key],
    };
  });
}

export function typeLabel(expenseType: string | null | undefined): string {
  if (!expenseType) return '';
  return categoryLabel(expenseType);
}

export function expenseApiError(err: unknown, fallback = 'Failed to load expenses'): string {
  const ax = err as {
    response?: { data?: { detail?: unknown }; status?: number };
    message?: string;
  };
  const detail = ax.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (ax.response?.status === 403) return 'Not enough permissions';
  if (ax.response?.status === 401) return 'Could not validate credentials';
  if (!ax.response) return 'Could not reach the expenses API';
  return ax.message || fallback;
}
