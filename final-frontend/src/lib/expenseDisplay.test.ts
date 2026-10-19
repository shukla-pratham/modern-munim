import { describe, expect, it } from 'vitest';
import {
  buildExpenseCreatePayload,
  buildExpenseUpdatePayload,
  expenseApiError,
  totalsByCategory,
  typeLabel,
} from '@/lib/expenseDisplay';
import type { ExpenseResponse } from '@/lib/api';

function row(partial: Partial<ExpenseResponse>): ExpenseResponse {
  return {
    id: 1,
    category: 'operations',
    description: 'Rent',
    amount: 100,
    expense_type: 'recurring',
    product_id: null,
    product_name: null,
    created_at: '2026-08-01T00:00:00Z',
    ...partial,
  };
}

describe('expenseDisplay', () => {
  it('totalsByCategory always emits all defined categories and never mock departments', () => {
    const totals = totalsByCategory([
      row({ category: 'operations', amount: 50 }),
      row({ id: 2, category: 'marketing', amount: '30' as unknown as number }),
    ]);
    expect(totals.map((t) => t.key)).toEqual(['inventory', 'operations', 'marketing', 'salary', 'miscellaneous']);
    expect(totals.map((t) => t.name)).toEqual(['Inventory', 'Operations', 'Marketing', 'Salary', 'Miscellaneous']);
    expect(totals.map((t) => t.actual)).toEqual([0, 50, 30, 0, 0]);
    expect(totals.map((t) => t.count)).toEqual([0, 1, 1, 0, 0]);
    expect(totals.some((t) => t.name === 'Procurement' || t.name === 'Logistics')).toBe(false);
  });

  it('totalsByCategory treats empty list as zero spend', () => {
    const totals = totalsByCategory([]);
    expect(totals.every((t) => t.actual === 0 && t.count === 0)).toBe(true);
  });

  it('typeLabel presents API enum values without renaming them', () => {
    expect(typeLabel('one_time')).toBe('One Time');
    expect(typeLabel('recurring')).toBe('Recurring');
  });

  it('buildExpenseCreatePayload sends lowercase API enums', () => {
    const result = buildExpenseCreatePayload({
      category: 'operations',
      description: 'Rent',
      amount: '100',
      expenseType: 'recurring',
      productId: '',
    });
    expect(result).toEqual({
      ok: true,
      body: {
        category: 'operations',
        description: 'Rent',
        amount: 100,
        expense_type: 'recurring',
      },
    });
  });

  it('buildExpenseUpdatePayload includes product_id when provided', () => {
    const result = buildExpenseUpdatePayload({
      category: 'inventory',
      description: 'Fee',
      amount: '12.5',
      expenseType: 'one_time',
      productId: '10',
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.body).toEqual({
        category: 'inventory',
        description: 'Fee',
        amount: 12.5,
        expense_type: 'one_time',
        product_id: 10,
      });
    }
  });

  it('buildExpenseCreatePayload rejects invalid amount', () => {
    const result = buildExpenseCreatePayload({
      category: 'marketing',
      description: 'Ads',
      amount: '-1',
      expenseType: 'one_time',
      productId: '',
    });
    expect(result.ok).toBe(false);
  });

  it('expenseApiError prefers Spring detail and 403 copy', () => {
    expect(expenseApiError({ response: { status: 403, data: { detail: 'Not enough permissions' } } }))
      .toBe('Not enough permissions');
    expect(expenseApiError({ message: 'Network Error' })).toBe('Could not reach the expenses API');
  });

  it('expenseApiError maps 401 without crashing', () => {
    expect(expenseApiError({ response: { status: 401 } })).toBe('Could not validate credentials');
  });

  it('buildExpenseCreatePayload rejects non-integer product_id', () => {
    const result = buildExpenseCreatePayload({
      category: 'inventory',
      description: 'Fee',
      amount: '1',
      expenseType: 'one_time',
      productId: '1.5',
    });
    expect(result.ok).toBe(false);
  });

  it('buildExpenseUpdatePayload never sends uppercase Java enum names', () => {
    const result = buildExpenseUpdatePayload({
      category: 'marketing',
      description: 'Ads',
      amount: '20',
      expenseType: 'recurring',
      productId: '',
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.body.category).toBe('marketing');
      expect(result.body.expense_type).toBe('recurring');
      expect(JSON.stringify(result.body)).not.toMatch(/INVENTORY|OPERATIONS|MARKETING|ONE_TIME|RECURRING/);
    }
  });
});
