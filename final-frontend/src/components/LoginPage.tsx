import { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, Store, ArrowRight, Loader2, ShieldCheck, Trash2 } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { DeleteStoreModal } from '@/components/DeleteStoreModal';
import {
  STORE_TYPES,
  canSubmitOnboarding,
  type AuthStep,
} from '@/lib/authFlow';

function apiErrorMessage(err: unknown, fallback: string): string {
  const ax = err as {
    code?: string;
    response?: { status?: number; data?: { detail?: unknown; error?: string } };
    message?: string;
  };
  if (!ax.response) {
    // Axios sets code='ECONNABORTED' for request timeouts (timeout option exceeded).
    if (ax.code === 'ECONNABORTED') {
      return 'The server is taking longer than expected. It may be waking up — please try again in a moment.';
    }
    // ERR_NETWORK covers DNS failures, refused connections, and offline state.
    if (ax.code === 'ERR_NETWORK') {
      return 'Network error: could not reach the server. Check your internet connection and try again.';
    }
    return 'Could not connect to the server. Please try again.';
  }
  const status = ax.response.status;
  if (status === 401) {
    return 'Incorrect email or password.';
  }
  if (status === 403) {
    return 'Access denied. Your account does not have permission to sign in here.';
  }
  if (status != null && status >= 500) {
    return 'The server encountered an error. Please try again shortly.';
  }
  const data = ax.response.data ?? {};
  if (typeof data.error === 'string' && data.error.trim() && data.error !== 'Validation failed') {
    return data.error;
  }
  const d = data.detail;
  if (Array.isArray(d)) {
    return (d as { msg?: string; message?: string }[])
      .map((x) => x?.msg ?? x?.message ?? JSON.stringify(x))
      .join('. ');
  }
  if (typeof d === 'object' && d !== null && 'message' in d) {
    return String((d as { message: string }).message);
  }
  if (typeof d === 'string' && d.trim()) return d;
  return ax.message || fallback;
}

export default function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [storeName, setStoreName] = useState('');
  const [storeType, setStoreType] = useState('');
  const [step, setStep] = useState<AuthStep>('credentials');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Multi-store state
  const [userStores, setUserStores] = useState<any[]>([]);
  const [showAddStoreForm, setShowAddStoreForm] = useState(false);
  const [newStoreName, setNewStoreName] = useState('');
  const [newStoreType, setNewStoreType] = useState('General Retail');

  const [deletingStoreId, setDeletingStoreId] = useState<number | null>(null);
  const [deleteTargetStore, setDeleteTargetStore] = useState<{ id: number; name: string } | null>(null);

  const {
    startAuth,
    completeOnboarding,
    resetPassword,
    selectWorkspace,
    createStoreWorkspace,
    deleteStoreWorkspace,
    workspaces,
  } = useAuth();

  const resetToCredentials = () => {
    setStep('credentials');
    setError('');
    setNotice('');
    setStoreName('');
    setStoreType('');
    setNewPassword('');
    setConfirmPassword('');
    setShowAddStoreForm(false);
  };

  // Called after JWT is issued and workspace list has ≤1 entries (auto-enter)
  const handleLoginSuccess = () => {
    onLogin();
  };

  // Called when startAuth returns 'authenticated' with multi-store
  const handleAuthenticated = (stores: any[]) => {
    if (stores.length > 1) {
      setUserStores(stores);
      setStep('store_select');
    } else {
      onLogin();
    }
  };

  const handleCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setNotice('');
    setLoading(true);
    try {
      const result = await startAuth(email, password, handleLoginSuccess);
      if (result.status === 'needs_onboarding') {
        setNotice(result.message);
        setStep('onboarding');
      } else if (result.status === 'authenticated') {
        // Multi-store check: workspaces already populated by startAuth
        const stores = (result as any).workspaces ?? [];
        handleAuthenticated(stores);
      }
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Could not continue'));
    } finally {
      setLoading(false);
    }
  };

  const handleOnboarding = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!canSubmitOnboarding(storeName, storeType)) {
      setError('Store name and store type are required.');
      return;
    }
    setLoading(true);
    try {
      await completeOnboarding(email, password, storeName, storeType, handleLoginSuccess);
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Could not create account'));
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setError(
      'Self-service password reset is disabled for account security. Please contact your workspace administrator to reset your password.'
    );
  };

  const handleChooseStore = (storeId: number) => {
    selectWorkspace(storeId);
    onLogin();
  };

  const handleCreateStore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStoreName.trim()) {
      setError('Store name is required');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const newWs = await createStoreWorkspace({
        name: newStoreName.trim(),
        store_type: newStoreType,
      });
      selectWorkspace(newWs.id);
      onLogin();
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Could not create store'));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteStore = (storeId: number, storeName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (userStores.length <= 1) {
      setError('You must have at least one store.');
      return;
    }
    setDeleteTargetStore({ id: storeId, name: storeName });
  };

  const handleStoreDeleted = (deletedId: number) => {
    const remaining = userStores.filter((s) => s.id !== deletedId);
    setUserStores(remaining);
    setDeleteTargetStore(null);
    if (remaining.length === 1) {
      handleChooseStore(remaining[0].id);
    }
  };

  const subtitle =
    step === 'credentials'
      ? 'Sign in with your email and password.'
      : step === 'forgot_password'
        ? 'Enter your email and a new password to reset your account.'
        : step === 'onboarding'
          ? "Looks like you're new here. Tell us about your store."
          : step === 'store_select'
            ? 'Select which store workspace you want to manage, or create a new store.'
            : '';

  return (
    <div className="min-h-screen flex items-center justify-center bg-background noise-bg relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-20 blur-3xl bg-primary" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 rounded-full opacity-10 blur-3xl bg-data" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md mx-4"
      >
        <div className="bg-card border border-border rounded-2xl p-8 card-shadow">
          <div className="flex flex-col items-center mb-8">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary to-data flex items-center justify-center font-bold text-xl text-primary-foreground mb-4">
              MM
            </div>
            <h1 className="text-2xl font-bold text-foreground">
              {step === 'onboarding'
                ? "Looks like you're new here."
                : step === 'forgot_password'
                  ? 'Reset Password'
                  : step === 'store_select'
                    ? 'Choose Your Store'
                    : 'Welcome / Sign In'}
            </h1>
            <p className="text-xs text-muted-foreground mt-2 text-center">{subtitle}</p>
          </div>

          {/* ── Credentials step ─────────────────────────────── */}
          {step === 'credentials' && (
            <form onSubmit={handleCredentials} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                    placeholder="you@example.com"
                    className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    id="login-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    autoComplete="current-password"
                    placeholder="At least 8 characters"
                    className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>
              {error && <div className="p-3 rounded-lg bg-destructive/15 text-destructive text-sm">{error}</div>}
              <motion.button
                id="login-submit"
                type="submit"
                disabled={loading}
                whileTap={{ scale: 0.97 }}
                className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium text-sm flex items-center justify-center gap-2 hover:opacity-90 transition-opacity mt-2 disabled:opacity-70"
              >
                {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Signing in…</> : <>Sign In <ArrowRight className="w-4 h-4" /></>}
              </motion.button>
              {loading && (
                <p className="text-xs text-muted-foreground text-center">
                  Connecting to server; the first request may take a moment.
                </p>
              )}
              <button
                type="button"
                className="w-full text-xs text-primary hover:underline"
                onClick={() => {
                  setError('');
                  setNotice('');
                  setNewPassword('');
                  setConfirmPassword('');
                  setStep('forgot_password');
                }}
              >
                Forgot password?
              </button>
            </form>
          )}

          {/* ── Forgot password step ──────────────────────────── */}
          {step === 'forgot_password' && (
            <form onSubmit={handleForgotPassword} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    id="forgot-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                    placeholder="you@example.com"
                    className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">New Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    id="forgot-new-password"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    placeholder="At least 8 characters"
                    className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    id="forgot-confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    placeholder="Repeat new password"
                    className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>
              {error && <div className="p-3 rounded-lg bg-destructive/15 text-destructive text-sm">{error}</div>}
              <motion.button
                id="forgot-submit"
                type="submit"
                disabled={loading}
                whileTap={{ scale: 0.97 }}
                className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium text-sm flex items-center justify-center gap-2 disabled:opacity-70"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Reset & Sign In <ShieldCheck className="w-4 h-4" /></>}
              </motion.button>
              <button
                type="button"
                className="w-full text-xs text-muted-foreground hover:text-foreground"
                onClick={resetToCredentials}
              >
                Back to sign in
              </button>
            </form>
          )}

          {/* ── Onboarding step ───────────────────────────────── */}
          {step === 'onboarding' && (
            <form onSubmit={handleOnboarding} className="space-y-4">
              <p className="text-sm text-muted-foreground text-center">Tell us about your store.</p>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">Store Name</label>
                <div className="relative">
                  <Store className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    id="onboard-store-name"
                    type="text"
                    value={storeName}
                    onChange={(e) => setStoreName(e.target.value)}
                    required
                    minLength={2}
                    autoComplete="organization"
                    placeholder="My Store"
                    className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">Store Type</label>
                <select
                  id="onboard-store-type"
                  value={storeType}
                  onChange={(e) => setStoreType(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="" disabled>
                    Select store type
                  </option>
                  {STORE_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              {error && <div className="p-3 rounded-lg bg-destructive/15 text-destructive text-sm">{error}</div>}
              <motion.button
                id="onboard-submit"
                type="submit"
                disabled={loading || !canSubmitOnboarding(storeName, storeType)}
                whileTap={{ scale: 0.97 }}
                className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium text-sm flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-70"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Create Account <ArrowRight className="w-4 h-4" /></>}
              </motion.button>
              <button
                type="button"
                className="w-full text-xs text-muted-foreground hover:text-foreground"
                onClick={resetToCredentials}
              >
                Back
              </button>
            </form>
          )}

          {/* ── Store select step ─────────────────────────────── */}
          {step === 'store_select' && (
            <div className="space-y-4">
              <div className="text-center space-y-1 mb-2">
                <p className="text-xs text-muted-foreground">
                  Logged in as <span className="text-foreground font-medium">{email}</span>
                </p>
                <p className="text-sm font-semibold text-foreground">
                  Which store do you want to access?
                </p>
              </div>

              {error && <div className="p-3 rounded-lg bg-destructive/15 text-destructive text-sm">{error}</div>}

              {!showAddStoreForm ? (
                <>
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {userStores.map((st) => (
                      <div
                        key={st.id}
                        onClick={() => handleChooseStore(st.id)}
                        className="w-full flex items-center justify-between p-3.5 rounded-xl border border-border bg-secondary hover:border-primary/50 hover:bg-accent text-left transition-all cursor-pointer group"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-9 h-9 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary group-hover:scale-105 transition-transform shrink-0">
                            <Store className="w-4 h-4" />
                          </div>
                          <div className="min-w-0">
                            <div className="font-semibold text-sm text-foreground truncate">{st.name}</div>
                            <div className="text-xs text-muted-foreground truncate">{st.store_type || 'General Retail'} • {st.role || 'Owner'}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0 ml-2">
                          {userStores.length > 1 && (
                            <button
                              type="button"
                              title="Delete store"
                              disabled={deletingStoreId === st.id}
                              onClick={(e) => handleDeleteStore(st.id, st.name, e)}
                              className="p-1.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors opacity-70 group-hover:opacity-100"
                            >
                              {deletingStoreId === st.id ? (
                                <Loader2 className="w-4 h-4 animate-spin text-destructive" />
                              ) : (
                                <Trash2 className="w-4 h-4" />
                              )}
                            </button>
                          )}
                          <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-border space-y-2">
                    <button
                      type="button"
                      onClick={() => { setShowAddStoreForm(true); setError(''); }}
                      className="w-full py-2.5 rounded-lg border border-dashed border-primary/50 hover:border-primary bg-primary/5 text-primary text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                    >
                      <Store className="w-4 h-4" />
                      + Add New Store
                    </button>
                    <button
                      type="button"
                      className="w-full text-xs text-muted-foreground hover:text-foreground pt-1"
                      onClick={resetToCredentials}
                    >
                      Sign Out / Switch Account
                    </button>
                  </div>
                </>
              ) : (
                <form onSubmit={handleCreateStore} className="space-y-4">
                  <div className="p-3 rounded-xl bg-primary/5 border border-primary/20">
                    <h3 className="text-xs font-semibold text-primary uppercase tracking-wider mb-1">
                      New Store Workspace
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      Each store maintains its own independent inventory, expenses, vendors, and orders.
                    </p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground mb-1.5 block">Store Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Downtown Branch, Store B"
                      value={newStoreName}
                      onChange={(e) => setNewStoreName(e.target.value)}
                      required
                      minLength={2}
                      className="w-full px-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground mb-1.5 block">Store Type</label>
                    <select
                      value={newStoreType}
                      onChange={(e) => setNewStoreType(e.target.value)}
                      required
                      className="w-full px-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    >
                      {STORE_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>

                  <motion.button
                    type="submit"
                    disabled={loading || !newStoreName.trim()}
                    whileTap={{ scale: 0.97 }}
                    className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium text-sm flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-70"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Create &amp; Enter Store <ArrowRight className="w-4 h-4" /></>}
                  </motion.button>

                  <button
                    type="button"
                    className="w-full text-xs text-muted-foreground hover:text-foreground"
                    onClick={() => { setShowAddStoreForm(false); setError(''); }}
                  >
                    Back to Store List
                  </button>
                </form>
              )}
            </div>
          )}

        </div>
      </motion.div>

      <DeleteStoreModal
        isOpen={!!deleteTargetStore}
        storeId={deleteTargetStore?.id ?? null}
        storeName={deleteTargetStore?.name ?? ''}
        onClose={() => setDeleteTargetStore(null)}
        onSuccess={handleStoreDeleted}
      />
    </div>
  );
}
