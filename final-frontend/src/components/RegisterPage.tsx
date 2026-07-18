import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, User, ArrowRight, Loader2 } from 'lucide-react';
import { authAPI } from '@/lib/api';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authAPI.register(email, password);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: unknown; error?: string }; status?: number }; message?: string };
      if (!ax.response) {
        setError('Could not connect to server. Is the backend running at http://localhost:8000?');
        return;
      }
      const data = ax.response.data ?? {};
      // Backend HTTP errors use "error"; validation uses "detail" (string or array)
      const errStr = typeof data.error === 'string' ? data.error : null;
      const d = data.detail;
      const msg =
        errStr ||
        (Array.isArray(d)
          ? (d as { msg?: string; message?: string }[]).map((x) => x?.msg ?? x?.message ?? JSON.stringify(x)).join('. ')
          : typeof d === 'object' && d !== null && (d as { message?: string }).message != null
            ? String((d as { message: string }).message)
            : typeof d === 'string'
              ? d
              : null);
      setError(msg || 'Registration failed. Try a different email or password.');
    } finally {
      setLoading(false);
    }
  };

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
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary to-data flex items-center justify-center font-bold text-xl text-primary-foreground mb-4">MM</div>
            <h1 className="text-2xl font-bold text-foreground">Create account</h1>
          </div>
          {error && <div className="mb-4 p-3 rounded-lg bg-destructive/15 text-destructive text-sm">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">Email</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
            </div>
            <motion.button
              type="submit"
              disabled={loading}
              whileTap={{ scale: 0.97 }}
              className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium text-sm flex items-center justify-center gap-2 hover:opacity-90 transition-opacity mt-6 disabled:opacity-70"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Register <ArrowRight className="w-4 h-4" /></>}
            </motion.button>
          </form>
          <p className="text-xs text-muted-foreground text-center mt-6">
            <Link to="/" className="text-primary hover:underline">Already have an account? Sign in</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
