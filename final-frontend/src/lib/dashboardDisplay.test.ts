import { describe, expect, it } from 'vitest';
import {
  apiErrorMessage,
  categoryLabel,
  expensePieData,
  periodLabel,
  salesTrendPoints,
  toNumber,
} from '@/lib/dashboardDisplay';

describe('dashboardDisplay', () => {
  it('toNumber treats nullish and invalid values as 0', () => {
    expect(toNumber(null)).toBe(0);
    expect(toNumber(undefined)).toBe(0);
    expect(toNumber('')).toBe(0);
    expect(toNumber('12.50')).toBe(12.5);
    expect(toNumber(80)).toBe(80);
  });

  it('periodLabel matches FastAPI last_N_days', () => {
    expect(periodLabel('last_30_days')).toBe('Last 30 days');
    expect(periodLabel('last_1_days')).toBe('Last 1 days');
    expect(periodLabel(undefined)).toBe('Last 30 days');
  });

  it('expensePieData always emits all defined categories and never mock categories', () => {
    const slices = expensePieData({ inventory: 50, operations: 30, marketing: 0, salary: 100, miscellaneous: 20 });
    expect(slices.map((s) => s.key)).toEqual(['inventory', 'operations', 'marketing', 'salary', 'miscellaneous']);
    expect(slices.map((s) => s.name)).toEqual(['Inventory', 'Operations', 'Marketing', 'Salary', 'Miscellaneous']);
    expect(slices.map((s) => s.value)).toEqual([50, 30, 0, 100, 20]);
    expect(slices.some((s) => s.name === 'Raw Materials')).toBe(false);
  });

  it('expensePieData fills missing keys with 0', () => {
    expect(expensePieData({})).toEqual([
      expect.objectContaining({ key: 'inventory', value: 0 }),
      expect.objectContaining({ key: 'operations', value: 0 }),
      expect.objectContaining({ key: 'marketing', value: 0 }),
      expect.objectContaining({ key: 'salary', value: 0 }),
      expect.objectContaining({ key: 'miscellaneous', value: 0 }),
    ]);
  });

  it('salesTrendPoints maps API revenue to the existing sales chart key', () => {
    expect(salesTrendPoints([{ date: '2026-08-10', orders: 2, revenue: 40 }])).toEqual([
      { date: '2026-08-10', orders: 2, sales: 40 },
    ]);
    expect(salesTrendPoints([])).toEqual([]);
  });

  it('categoryLabel title-cases snake_case keys', () => {
    expect(categoryLabel('one_time')).toBe('One Time');
  });

  it('apiErrorMessage prefers Spring detail and 403 copy', () => {
    expect(apiErrorMessage({ response: { status: 403, data: { detail: 'Not enough permissions' } } }, 'x'))
      .toBe('Not enough permissions');
    expect(apiErrorMessage({ response: { status: 401, data: { detail: 'Could not validate credentials' } } }, 'x'))
      .toBe('Could not validate credentials');
    expect(apiErrorMessage({ message: 'Network Error' }, 'fallback')).toBe('Could not reach the dashboard API');
  });
});
