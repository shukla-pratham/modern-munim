import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon, Gauge, RotateCcw, Eye, BarChart3, Store, Mail, KeyRound, Loader2, AlertTriangle } from 'lucide-react';
import { useAppSettings } from '@/contexts/SettingsContext';
import { useAuth } from '@/lib/auth-context';
import { authAPI } from '@/lib/api';

export default function SettingsPage() {
  const { settings, updateSettings, resetData } = useAppSettings();
  const { user } = useAuth();

  const [showResetModal, setShowResetModal] = useState(false);
  const [otpStep, setOtpStep] = useState<'idle' | 'otp_sent'>('idle');
  const [otpCode, setOtpCode] = useState('');
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

  const handleOpenReset = () => {
    setShowResetModal(true);
    setOtpStep('idle');
    setOtpCode('');
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  const handleCloseReset = () => {
    setShowResetModal(false);
    setOtpStep('idle');
    setOtpCode('');
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  const handleRequestOtp = async () => {
    if (!user?.email) {
      setErrorMsg('No user email found to send verification code.');
      return;
    }
    setIsSendingOtp(true);
    setErrorMsg(null);
    try {
      await authAPI.resendOtp(user.email);
      setOtpStep('otp_sent');
      setSuccessMsg(`Verification code sent to ${user.email}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to send OTP code. Please try again.';
      setErrorMsg(msg);
    } finally {
      setIsSendingOtp(false);
    }
  };

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.email) return;
    if (!otpCode.trim() || otpCode.trim().length !== 6) {
      setErrorMsg('Please enter the 6-digit verification code.');
      return;
    }
    setIsVerifying(true);
    setErrorMsg(null);
    try {
      await authAPI.verifyOtp(user.email, otpCode.trim());
      resetData();
      setShowResetModal(false);
      window.location.reload();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Invalid verification code. Please check and try again.';
      setErrorMsg(msg);
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="max-w-2xl space-y-6">
      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          <Store className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Account</h3>
        </div>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-muted-foreground">Email</dt>
            <dd className="text-foreground font-medium text-right">{user?.email || '—'}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted-foreground">Role</dt>
            <dd className="text-foreground font-medium text-right">{user?.role || '—'}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted-foreground">Store name</dt>
            <dd className="text-foreground font-medium text-right">{user?.store_name || '—'}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted-foreground">Store type</dt>
            <dd className="text-foreground font-medium text-right">{user?.store_type || '—'}</dd>
          </div>
        </dl>
        <p className="text-xs text-muted-foreground mt-4">
          Sign-in uses email + password + email OTP. This app is admin-only.
        </p>
      </motion.div>

      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          {settings.theme === 'dark' ? <Moon className="w-5 h-5 text-primary" /> : <Sun className="w-5 h-5 text-primary" />}
          <h3 className="font-semibold text-foreground">Theme</h3>
        </div>
        <div className="flex gap-3">
          {(['dark', 'light'] as const).map((t) => (
            <button
              key={t}
              onClick={() => updateSettings({ theme: t })}
              className={`flex-1 px-4 py-3 rounded-lg text-sm font-medium transition-all border ${
                settings.theme === t ? 'bg-primary text-primary-foreground border-primary' : 'bg-secondary text-muted-foreground border-border hover:text-foreground'
              }`}
            >
              {t === 'dark' ? 'Dark' : 'Light'}
            </button>
          ))}
        </div>
      </motion.div>

      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          <Eye className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Reduced Motion</h3>
        </div>
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">Disable heavy animations and transitions</p>
          <button
            onClick={() => updateSettings({ reducedMotion: !settings.reducedMotion })}
            className={`relative w-12 h-6 rounded-full transition-colors ${settings.reducedMotion ? 'bg-primary' : 'bg-secondary'}`}
          >
            <motion.div
              animate={{ x: settings.reducedMotion ? 24 : 2 }}
              className="absolute top-1 w-4 h-4 bg-primary-foreground rounded-full shadow"
            />
          </button>
        </div>
      </motion.div>

      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          <Gauge className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Animation Intensity</h3>
        </div>
        <div className="flex gap-3">
          {(['minimal', 'balanced', 'expressive'] as const).map((level) => (
            <button
              key={level}
              onClick={() => updateSettings({ animationIntensity: level })}
              className={`flex-1 px-3 py-2.5 rounded-lg text-sm font-medium transition-all border capitalize ${
                settings.animationIntensity === level ? 'bg-primary text-primary-foreground border-primary' : 'bg-secondary text-muted-foreground border-border hover:text-foreground'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </motion.div>

      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Chart Density</h3>
        </div>
        <div className="flex gap-3">
          {(['compact', 'comfortable', 'spacious'] as const).map((d) => (
            <button
              key={d}
              onClick={() => updateSettings({ chartDensity: d })}
              className={`flex-1 px-3 py-2.5 rounded-lg text-sm font-medium transition-all border capitalize ${
                settings.chartDensity === d ? 'bg-primary text-primary-foreground border-primary' : 'bg-secondary text-muted-foreground border-border hover:text-foreground'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </motion.div>

      <motion.div variants={fadeUp}>
        <button
          onClick={handleOpenReset}
          className="flex items-center gap-2 px-4 py-2.5 bg-destructive text-destructive-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
        >
          <RotateCcw className="w-4 h-4" />
          Reset App Data
        </button>
      </motion.div>

      {/* Confirmation & OTP Modal */}
      <AnimatePresence>
        {showResetModal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/60 backdrop-blur-sm z-50"
              onClick={handleCloseReset}
            />
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto pointer-events-none">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full max-w-md bg-card border border-border rounded-xl shadow-xl p-6 pointer-events-auto my-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center gap-3 text-destructive mb-3">
                  <AlertTriangle className="w-6 h-6 shrink-0" />
                  <h3 className="font-semibold text-foreground text-lg">Reset App Data Confirmation</h3>
                </div>


              <p className="text-sm text-muted-foreground mb-4">
                This will reset your local preferences, settings cache, and cached session data. For security, an email OTP verification is required before executing this reset.
              </p>

              {errorMsg && (
                <div className="p-3 mb-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                  {errorMsg}
                </div>
              )}

              {successMsg && (
                <div className="p-3 mb-4 rounded-lg bg-primary/10 border border-primary/20 text-primary text-sm flex items-center gap-2">
                  <Mail className="w-4 h-4 shrink-0" />
                  <span>{successMsg}</span>
                </div>
              )}

              {otpStep === 'idle' ? (
                <div className="space-y-4">
                  <div className="bg-secondary/40 rounded-lg p-3 text-sm text-foreground">
                    <p className="font-medium mb-1">Target Account:</p>
                    <p className="text-muted-foreground">{user?.email || 'Unknown'}</p>
                  </div>
                  <div className="flex gap-3 justify-end pt-2">
                    <button
                      type="button"
                      onClick={handleCloseReset}
                      className="px-4 py-2 rounded-lg border border-border bg-card text-foreground hover:bg-accent text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleRequestOtp}
                      disabled={isSendingOtp}
                      className="px-4 py-2 rounded-lg bg-destructive text-destructive-foreground font-medium hover:bg-destructive/90 disabled:opacity-50 text-sm flex items-center gap-2"
                    >
                      {isSendingOtp ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                      {isSendingOtp ? 'Sending OTP…' : 'Send Verification OTP'}
                    </button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleConfirmReset} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">
                      Enter 6-Digit Verification Code
                    </label>
                    <div className="relative">
                      <KeyRound className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                      <input
                        type="text"
                        maxLength={6}
                        value={otpCode}
                        onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                        placeholder="123456"
                        autoFocus
                        className="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-lg text-foreground text-center tracking-widest font-mono text-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <button
                      type="button"
                      onClick={handleRequestOtp}
                      disabled={isSendingOtp}
                      className="text-xs text-primary hover:underline flex items-center gap-1 disabled:opacity-50"
                    >
                      {isSendingOtp && <Loader2 className="w-3 h-3 animate-spin" />}
                      Resend code
                    </button>

                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={handleCloseReset}
                        className="px-4 py-2 rounded-lg border border-border bg-card text-foreground hover:bg-accent text-sm"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={isVerifying || otpCode.length !== 6}
                        className="px-4 py-2 rounded-lg bg-destructive text-destructive-foreground font-medium hover:bg-destructive/90 disabled:opacity-50 text-sm flex items-center gap-2"
                      >
                        {isVerifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
                        {isVerifying ? 'Verifying…' : 'Verify & Reset'}
                      </button>
                    </div>
                  </div>
                </form>
              )}
            </motion.div>
          </div>
        </>
      )}

      </AnimatePresence>
    </motion.div>
  );
}

