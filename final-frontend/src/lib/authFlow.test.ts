import { describe, it, expect } from 'vitest';
import {
  STORE_TYPES,
  canSubmitOnboarding,
  nextStepAfterStart,
  isAdminRole,
} from './authFlow';

describe('authFlow', () => {
  it('new email start status goes to onboarding', () => {
    expect(nextStepAfterStart('needs_onboarding')).toBe('onboarding');
  });

  it('existing email start status goes to otp (skips store fields)', () => {
    expect(nextStepAfterStart('otp_sent')).toBe('otp');
  });

  it('rejects missing store name', () => {
    expect(canSubmitOnboarding('', 'Bakery')).toBe(false);
    expect(canSubmitOnboarding('A', 'Bakery')).toBe(false);
  });

  it('rejects missing / invalid store type', () => {
    expect(canSubmitOnboarding('My Store', '')).toBe(false);
    expect(canSubmitOnboarding('My Store', 'NotReal')).toBe(false);
  });

  it('accepts valid onboarding fields including non-bakery types', () => {
    expect(canSubmitOnboarding('My Store', 'Electronics')).toBe(true);
    expect(STORE_TYPES).toContain('Grocery');
    expect(STORE_TYPES).toContain('Pharmacy');
  });

  it('admin role check', () => {
    expect(isAdminRole('admin')).toBe(true);
    expect(isAdminRole('ADMIN')).toBe(true);
    expect(isAdminRole('customer')).toBe(false);
    expect(isAdminRole(null)).toBe(false);
  });
});
