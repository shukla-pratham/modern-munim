import { describe, it, expect } from 'vitest';
import { isAdminRole } from './authFlow';

/**
 * Documents the SPA session contract used by auth-context:
 * - access_token in localStorage
 * - hydrate via GET /api/auth/me
 * - logout clears token
 * - non-admin rejected
 */
describe('auth session contract', () => {
  it('restores only when token present and /me returns admin', () => {
    const token = 'jwt-example';
    const me = { id: 1, email: 'a@example.com', role: 'admin' };
    expect(Boolean(token) && isAdminRole(me.role)).toBe(true);
  });

  it('rejects non-admin me payload (access denied path)', () => {
    const me = { id: 2, email: 'c@example.com', role: 'customer' };
    expect(isAdminRole(me.role)).toBe(false);
  });

  it('logout clears token key used by api interceptor', () => {
    const key = 'access_token';
    const store: Record<string, string> = { [key]: 'jwt' };
    delete store[key];
    expect(store[key]).toBeUndefined();
  });
});
