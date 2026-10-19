import { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, Loader2, ShieldCheck } from 'lucide-react';
import { authAPI } from '@/lib/api';
import { PENDING_PASSWORD_RESET_KEY } from '@/lib/authFlow';

function apiErrorMessage(err: unknown, fallback: string): string {
  const ax = err as { response?: { data?: { detail?: unknown; error?: string } }; message?: string };
  if (!ax.response) return 'Could not connect to server.';
  const data = ax.response.data ?? {};
  if (typeof data.error === 'string' && data.error.trim() && data.error !== 'Validation failed') {
    return data.error;
  }
  const d = data.detail;
  if (typeof d === 'string' && d.trim()) return d;
  return ax.message || fallback;
}

/** Shown after forgot-password OTP login; must set a new password before using the app. */
export default function SetNewPasswordGate({ onDone }: { onDone: () => void }) {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await authAPI.updatePassword(password);
      sessionStorage.removeItem(PENDING_PASSWORD_RESET_KEY);
      onDone();
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Could not update password'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background noise-bg px-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-card border border-border rounded-2xl p-8 card-shadow"
      >
        <div className="flex flex-col items-center mb-6">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary to-data flex items-center justify-center font-bold text-xl text-primary-foreground mb-4">
            MM
          </div>
          <h1 className="text-2xl font-bold text-foreground">Set a new password</h1>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            You&apos;re signed in via email OTP. Choose a new password before continuing.
          </p>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground mb-1.5 block">New password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
                className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-foreground mb-1.5 block">Confirm password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
                className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>
          {error && <div className="p-3 rounded-lg bg-destructive/15 text-destructive text-sm">{error}</div>}
          <motion.button
            type="submit"
            disabled={loading}
            whileTap={{ scale: 0.97 }}
            className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium text-sm flex items-center justify-center gap-2 disabled:opacity-70"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Save password <ShieldCheck className="w-4 h-4" /></>}
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
}
