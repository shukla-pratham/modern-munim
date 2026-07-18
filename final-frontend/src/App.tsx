import { useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SettingsProvider, useAppSettings } from '@/contexts/SettingsContext';
import { AuthProvider, useAuth } from '@/lib/auth-context';
import CinematicIntro from '@/components/CinematicIntro';
import LoginPage from '@/components/LoginPage';
import RegisterPage from '@/components/RegisterPage';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import Inventory from '@/pages/Inventory';
import Vendors from '@/pages/Vendors';
import PurchaseOrders from '@/pages/PurchaseOrders';
import Expenses from '@/pages/Expenses';
import AIInsights from '@/pages/AIInsights';
import SettingsPage from '@/pages/Settings';

function AppContent() {
  const { updateSettings } = useAppSettings();
  const { user, loading, logout } = useAuth();
  const [showIntro, setShowIntro] = useState(true);

  const handleIntroComplete = useCallback(() => {
    setShowIntro(false);
    updateSettings({ introSeen: true });
  }, [updateSettings]);

  const handleLogin = useCallback(() => {}, []);
  const handleLogout = useCallback(() => logout(), [logout]);

  if (showIntro) return <CinematicIntro onComplete={handleIntroComplete} />;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<LoginPage onLogin={handleLogin} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    );
  }

  return (
    <Layout onLogout={handleLogout}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/vendors" element={<Vendors />} />
        <Route path="/purchase-orders" element={<PurchaseOrders />} />
        <Route path="/expenses" element={<Expenses />} />
        <Route path="/ai-insights" element={<AIInsights />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <SettingsProvider>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </SettingsProvider>
    </AuthProvider>
  );
}
