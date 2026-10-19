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

export type AuthStep = 'credentials' | 'onboarding' | 'otp' | 'store_select' | 'forgot_email';

export type AuthStartStatus = 'needs_onboarding' | 'otp_sent';

/** Set after forgot-password OTP login; cleared after new password is saved. */
export const PENDING_PASSWORD_RESET_KEY = 'pending_password_reset';

export function nextStepAfterStart(status: AuthStartStatus): AuthStep {
  if (status === 'needs_onboarding') return 'onboarding';
  return 'otp';
}

export function canSubmitOnboarding(storeName: string, storeType: string): boolean {
  return storeName.trim().length >= 2 && STORE_TYPES.includes(storeType as (typeof STORE_TYPES)[number]);
}

export function isAdminRole(role: string | undefined | null): boolean {
  return (role || '').toLowerCase() === 'admin';
}
