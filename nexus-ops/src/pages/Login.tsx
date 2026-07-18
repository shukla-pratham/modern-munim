import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Zap, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => navigate('/dashboard'), 1200);
  };

  const stagger = {
    hidden: {},
    show: { transition: { staggerChildren: 0.08 } },
  };
  const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } },
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/10" />
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/8 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-cyan/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '1.5s' }} />

      <motion.div
        className="relative z-10 w-full max-w-md mx-4"
        variants={stagger}
        initial="hidden"
        animate="show"
      >
        <motion.div className="glass-strong rounded-2xl p-8 shadow-2xl" variants={fadeUp}>
          {/* Logo */}
          <motion.div className="flex items-center justify-center gap-3 mb-8" variants={fadeUp}>
            <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center">
              <Zap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">FF Marketplace</span>
          </motion.div>

          <motion.p className="text-center text-sm text-muted-foreground mb-6" variants={fadeUp}>
            Sign in to your operations dashboard
          </motion.p>

          <form onSubmit={handleLogin} className="space-y-4">
            <motion.div className="space-y-2" variants={fadeUp}>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@ffmarketplace.com"
                defaultValue="admin@ffmarketplace.com"
                className="h-11 bg-background/50 border-border/60 focus:border-primary focus:glow-primary transition-shadow"
              />
            </motion.div>

            <motion.div className="space-y-2" variants={fadeUp}>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                defaultValue="password"
                className="h-11 bg-background/50 border-border/60 focus:border-primary focus:glow-primary transition-shadow"
              />
            </motion.div>

            <motion.button
              type="submit"
              disabled={loading}
              className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-medium text-sm flex items-center justify-center gap-2 transition-all hover:bg-primary/90 disabled:opacity-70"
              variants={fadeUp}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.97 }}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Sign In'
              )}
            </motion.button>
          </form>

          <motion.p className="text-xs text-muted-foreground text-center mt-6" variants={fadeUp}>
            Internal operations platform · Admin access only
          </motion.p>
        </motion.div>
      </motion.div>
    </div>
  );
}
