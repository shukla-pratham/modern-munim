/** Store types for new-admin onboarding (must match backend STORE_TYPES). */
export const STORE_TYPES = [
  'Bakery',
  'Confectionery',
  'Grocery',
  'Clothing',
  'Electronics',
  'Pharmacy',
  'Restaurant / Cafe',
  'General Retail',
  'Other',
] as const;

export type AuthStep = 'credentials' | 'onboarding' | 'store_select' | 'forgot_password';

export type AuthStartStatus = 'needs_onboarding' | 'authenticated';

export function nextStepAfterStart(status: AuthStartStatus): AuthStep {
  if (status === 'needs_onboarding') return 'onboarding';
  // 'authenticated' — JWT already issued, caller handles login completion
  return 'credentials';
}

export function canSubmitOnboarding(storeName: string, storeType: string): boolean {
  return storeName.trim().length >= 2 && STORE_TYPES.includes(storeType as (typeof STORE_TYPES)[number]);
}

export function isAdminRole(role: string | undefined | null): boolean {
  return (role || '').toLowerCase() === 'admin';
}
