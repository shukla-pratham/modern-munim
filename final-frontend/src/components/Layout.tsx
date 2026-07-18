import { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Package, Building2, FileText, DollarSign, Brain, Settings, LogOut,
  Menu, X, Sun, Moon, Plus, ChevronDown } from 'lucide-react';
import { useAppSettings } from '@/contexts/SettingsContext';

const navItems = [
{ to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
{ to: '/inventory', icon: Package, label: 'Inventory' },
{ to: '/vendors', icon: Building2, label: 'Vendors' },
{ to: '/purchase-orders', icon: FileText, label: 'Purchase Orders' },
{ to: '/expenses', icon: DollarSign, label: 'Expenses' },
{ to: '/ai-insights', icon: Brain, label: 'AI Insights' },
{ to: '/settings', icon: Settings, label: 'Settings' }];


export default function Layout({ children, onLogout }: {children: React.ReactNode;onLogout: () => void;}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [addMenuOpen, setAddMenuOpen] = useState(false);
  const { settings, updateSettings } = useAppSettings();
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="flex h-screen bg-background noise-bg overflow-hidden">
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen &&
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)} />

        }
      </AnimatePresence>

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-card border-r border-border flex flex-col transition-transform duration-300 lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center gap-3 px-5 h-16 border-b border-border">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-data flex items-center justify-center font-bold text-xs text-primary-foreground">MM

          </div>
          <span className="font-semibold text-foreground text-sm">Modern Munim</span>
          <button onClick={() => setSidebarOpen(false)} className="ml-auto lg:hidden text-muted-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {navItems.map((item) =>
          <NavLink
            key={item.to}
            to={item.to}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            isActive ?
            'bg-primary/10 text-primary' :
            'text-muted-foreground hover:text-foreground hover:bg-accent'}`

            }>

              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          )}
        </nav>

        <div className="p-3 border-t border-border space-y-1">
          <button
            onClick={() => updateSettings({ theme: settings.theme === 'dark' ? 'light' : 'dark' })}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent w-full transition-colors">

            {settings.theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            {settings.theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </button>
          <button
            onClick={onLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/10 w-full transition-colors">

            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="h-16 border-b border-border flex items-center px-4 gap-4 bg-card/50 backdrop-blur-sm">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-muted-foreground">
            <Menu className="w-5 h-5" />
          </button>
          <h2 className="text-lg font-semibold text-foreground capitalize flex-1">
            {location.pathname.split('/')[1]?.replace('-', ' ') || 'Dashboard'}
          </h2>
          <div className="relative">
            <button
              type="button"
              onClick={() => setAddMenuOpen((o) => !o)}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-card text-foreground text-sm font-medium hover:bg-accent"
            >
              <Plus className="w-4 h-4" />
              Add
              <ChevronDown className="w-4 h-4" />
            </button>
            <AnimatePresence>
              {addMenuOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setAddMenuOpen(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="absolute right-0 top-full mt-1 py-1 w-48 bg-card border border-border rounded-lg shadow-lg z-50"
                  >
                    <button
                      type="button"
                      onClick={() => { navigate('/inventory'); setAddMenuOpen(false); }}
                      className="flex items-center gap-2 w-full px-3 py-2 text-left text-sm text-foreground hover:bg-accent"
                    >
                      <Package className="w-4 h-4" />
                      Add SKU / Product
                    </button>
                    <button
                      type="button"
                      onClick={() => { navigate('/inventory'); setAddMenuOpen(false); }}
                      className="flex items-center gap-2 w-full px-3 py-2 text-left text-sm text-foreground hover:bg-accent"
                    >
                      <Package className="w-4 h-4" />
                      Adjust stock
                    </button>
                    <button
                      type="button"
                      onClick={() => { navigate('/vendors'); setAddMenuOpen(false); }}
                      className="flex items-center gap-2 w-full px-3 py-2 text-left text-sm text-foreground hover:bg-accent"
                    >
                      <Building2 className="w-4 h-4" />
                      Add vendor
                    </button>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="p-4 md:p-6 relative z-10">

            {children}
          </motion.div>
        </div>
      </main>
    </div>
  );
}