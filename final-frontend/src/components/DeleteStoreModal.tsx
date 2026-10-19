import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, KeyRound, Mail, Loader2, X, ShieldAlert } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

interface DeleteStoreModalProps {
  isOpen: boolean;
  storeId: number | null;
  storeName: string;
  onClose: () => void;
  onSuccess: (deletedId: number) => void;
}

export function DeleteStoreModal({
  isOpen,
  storeId,
  storeName,
  onClose,
  onSuccess,
}: DeleteStoreModalProps) {
  const { requestStoreDeleteOtp, deleteStoreWorkspace } = useAuth();
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<'initial' | 'otp_sent'>('initial');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  if (!isOpen || !storeId) return null;

  const handleSendOtp = async () => {
    if (!password) {
      setError('Please enter your account password to verify your identity.');
      return;
    }
    setError('');
    setNotice('');
    setLoading(true);
    try {
      const res = await requestStoreDeleteOtp(storeId);
      setNotice(res.message || 'Verification OTP sent to your registered email.');
      setStep('otp_sent');
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (err as { message?: string })?.message ??
        'Failed to send deletion OTP.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDelete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setError('Password is required.');
      return;
    }
    if (!otp.trim() || otp.trim().length !== 6) {
      setError('Please enter the 6-digit OTP sent to your email.');
      return;
    }

    setError('');
    setLoading(true);
    try {
      await deleteStoreWorkspace(storeId, {
        password,
        otp: otp.trim(),
      });
      onSuccess(storeId);
      handleClose();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (err as { message?: string })?.message ??
        'Failed to delete store workspace.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setPassword('');
    setOtp('');
    setStep('initial');
    setError('');
    setNotice('');
    onClose();
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 overflow-y-auto">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-background/80 backdrop-blur-sm"
          onClick={handleClose}
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 12 }}
          className="relative w-full max-w-md bg-card border border-destructive/30 rounded-xl shadow-2xl p-6 z-10 my-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-border">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-destructive/10 border border-destructive/20 flex items-center justify-center text-destructive">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground text-sm">Security Verification</h3>
                <p className="text-xs text-muted-foreground">Authorize Store Deletion</p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleClose}
              className="text-muted-foreground hover:text-foreground p-1 rounded-lg"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="p-3 mb-4 rounded-lg bg-destructive/10 border border-destructive/20 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
            <div className="text-xs text-destructive-foreground">
              You are about to permanently delete <strong className="font-bold underline">{storeName}</strong>.
              All associated inventory, orders, expenses, and settings will be permanently destroyed.
            </div>
          </div>

          {error && (
            <div className="p-3 mb-4 text-xs bg-destructive/10 border border-destructive/20 text-destructive rounded-lg">
              {error}
            </div>
          )}

          {notice && (
            <div className="p-3 mb-4 text-xs bg-primary/10 border border-primary/20 text-primary rounded-lg flex items-center gap-2">
              <Mail className="w-4 h-4 shrink-0" />
              {notice}
            </div>
          )}

          <form onSubmit={handleConfirmDelete} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-foreground mb-1.5 flex items-center gap-1.5">
                <KeyRound className="w-3.5 h-3.5 text-muted-foreground" />
                Account Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your account password"
                className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-destructive/50"
              />
            </div>

            {step === 'initial' ? (
              <div className="pt-2">
                <button
                  type="button"
                  disabled={loading || !password}
                  onClick={handleSendOtp}
                  className="w-full py-2.5 bg-primary text-primary-foreground font-medium text-sm rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2 transition-opacity shadow-sm"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Mail className="w-4 h-4" />
                      Send Verification OTP to Email
                    </>
                  )}
                </button>
              </div>
            ) : (
              <>
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-muted-foreground" />
                      6-Digit Email OTP
                    </span>
                    <button
                      type="button"
                      disabled={loading}
                      onClick={handleSendOtp}
                      className="text-[11px] text-primary hover:underline"
                    >
                      Resend Code
                    </button>
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="e.g. 123456"
                    className="w-full px-3 py-2 text-sm font-mono tracking-widest text-center bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-destructive/50"
                  />
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={handleClose}
                    className="flex-1 py-2 text-sm border border-border rounded-lg text-muted-foreground hover:text-foreground"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !password || otp.trim().length !== 6}
                    className="flex-1 py-2 bg-destructive text-destructive-foreground font-medium text-sm rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2 transition-opacity"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Confirm & Delete'}
                  </button>
                </div>
              </>
            )}
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
