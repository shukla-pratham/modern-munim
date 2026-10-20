/**
 * Focused tests for LoginPage error-state UX:
 * - timeout (ECONNABORTED)
 * - network error (ERR_NETWORK)
 * - generic no-response error
 * - HTTP 401 authentication failure
 * - HTTP 403 forbidden
 * - HTTP 5xx server error
 * - cold-start loading hint visibility
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from '@/components/LoginPage';

// Minimal stub for useAuth — only the fields LoginPage actually uses.
vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
}));

// Minimal stub for framer-motion — just render children as-is.
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...rest }: React.PropsWithChildren<object>) => <div {...rest}>{children}</div>,
    button: ({
      children,
      whileTap: _wt,
      ...rest
    }: React.PropsWithChildren<{ whileTap?: unknown } & React.ButtonHTMLAttributes<HTMLButtonElement>>) => (
      <button {...rest}>{children}</button>
    ),
  },
}));

import { useAuth } from '@/lib/auth-context';

function makeAuthStub(startAuth: (...args: unknown[]) => unknown) {
  return {
    startAuth,
    completeOnboarding: vi.fn(),
    resetPassword: vi.fn(),
    selectWorkspace: vi.fn(),
    createStoreWorkspace: vi.fn(),
    deleteStoreWorkspace: vi.fn(),
    workspaces: [],
  };
}

function axiosError(overrides: Record<string, unknown>) {
  return Object.assign(new Error('axios error'), overrides);
}

function renderLoginPage() {
  const onLogin = vi.fn();
  render(<LoginPage onLogin={onLogin} />);
  return { onLogin };
}

async function submitCredentials(email = 'test@example.com', password = 'password123') {
  fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
    target: { value: email },
  });
  fireEvent.change(screen.getByPlaceholderText('At least 8 characters'), {
    target: { value: password },
  });
  fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('LoginPage error states', () => {
  it('shows a timeout-specific message when the request times out (ECONNABORTED)', async () => {
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue(
      makeAuthStub(() => Promise.reject(axiosError({ code: 'ECONNABORTED' }))),
    );
    renderLoginPage();
    await submitCredentials();
    await waitFor(() => {
      expect(screen.getByText(/taking longer than expected/i)).toBeInTheDocument();
    });
  });

  it('shows a network-error message when there is no network (ERR_NETWORK)', async () => {
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue(
      makeAuthStub(() => Promise.reject(axiosError({ code: 'ERR_NETWORK' }))),
    );
    renderLoginPage();
    await submitCredentials();
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it('shows a generic connection message for unknown no-response errors', async () => {
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue(
      makeAuthStub(() => Promise.reject(axiosError({}))),
    );
    renderLoginPage();
    await submitCredentials();
    await waitFor(() => {
      expect(screen.getByText(/could not connect/i)).toBeInTheDocument();
    });
  });

  it('shows an auth-error message for HTTP 401', async () => {
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue(
      makeAuthStub(() =>
        Promise.reject(axiosError({ response: { status: 401, data: {} } })),
      ),
    );
    renderLoginPage();
    await submitCredentials();
    await waitFor(() => {
      expect(screen.getByText(/incorrect email or password/i)).toBeInTheDocument();
    });
  });

  it('shows a forbidden message for HTTP 403', async () => {
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue(
      makeAuthStub(() =>
        Promise.reject(axiosError({ response: { status: 403, data: {} } })),
      ),
    );
    renderLoginPage();
    await submitCredentials();
    await waitFor(() => {
      expect(screen.getByText(/access denied/i)).toBeInTheDocument();
    });
  });

  it('shows a server-error message for HTTP 500', async () => {
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue(
      makeAuthStub(() =>
        Promise.reject(axiosError({ response: { status: 500, data: {} } })),
      ),
    );
    renderLoginPage();
    await submitCredentials();
    await waitFor(() => {
      expect(screen.getByText(/server encountered an error/i)).toBeInTheDocument();
    });
  });

  it('shows the cold-start loading hint while a sign-in request is pending', async () => {
    let resolve!: () => void;
    const pendingPromise = new Promise<never>((_, rej) => { resolve = () => rej(new Error('cancelled')); });
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue(
      makeAuthStub(() => pendingPromise),
    );
    renderLoginPage();
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('At least 8 characters'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(
        screen.getByText(/connecting to server.*first request may take a moment/i),
      ).toBeInTheDocument();
    });
    // Clean up the pending promise
    resolve();
  });
});
