import { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Package, Building2, FileText, DollarSign, Brain, Settings, LogOut,
  Menu, X, Sun, Moon, Plus, ChevronDown, HelpCircle, Store, Check, Loader2, Trash2 } from 'lucide-react';

import { useAppSettings } from '@/contexts/SettingsContext';
import { useAuth } from '@/lib/auth-context';
import { STORE_TYPES } from '@/lib/authFlow';
import OnboardingTour from './OnboardingTour';
import { DeleteStoreModal } from './DeleteStoreModal';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inventory', icon: Package, label: 'Inventory' },
  { to: '/vendors', icon: Building2, label: 'Vendors' },
  { to: '/purchase-orders', icon: FileText, label: 'Purchase Orders' },
  { to: '/expenses', icon: DollarSign, label: 'Expenses' },
  { to: '/ai-insights', icon: Brain, label: 'AI Insights' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout({ children, onLogout }: { children: React.ReactNode; onLogout: () => void }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [addMenuOpen, setAddMenuOpen] = useState(false);
  const [storeMenuOpen, setStoreMenuOpen] = useState(false);
  const [showAddStoreModal, setShowAddStoreModal] = useState(false);
  const [deleteTargetStore, setDeleteTargetStore] = useState<{ id: number; name: string } | null>(null);
  const [newStoreName, setNewStoreName] = useState('');
  const [newStoreType, setNewStoreType] = useState('General Retail');
  const [storeLoading, setStoreLoading] = useState(false);
  const [storeError, setStoreError] = useState('');

  const [forceTour, setForceTour] = useState(false);
  const { settings, updateSettings } = useAppSettings();
  const {
    workspaces,
    activeWorkspace,
    selectWorkspace,
    createStoreWorkspace,
    deleteStoreWorkspace,
  } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleCreateStore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStoreName.trim()) {
      setStoreError('Store name is required.');
      return;
    }
    setStoreLoading(true);
    setStoreError('');
    try {
      const created = await createStoreWorkspace({
        name: newStoreName.trim(),
        store_type: newStoreType,
      });
      selectWorkspace(created.id);
      setShowAddStoreModal(false);
      setNewStoreName('');
      // Reload page data to reflect the newly switched store
      window.location.reload();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (err as { message?: string })?.message ??
        'Failed to create new store workspace.';
      setStoreError(msg);
    } finally {
      setStoreLoading(false);
    }
  };

  const handleDeleteStore = (storeId: number, storeName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (workspaces.length <= 1) {
      alert('You must have at least one store.');
      return;
    }
    setStoreMenuOpen(false);
    setDeleteTargetStore({ id: storeId, name: storeName });
  };

  const handleSwitchStore = (wid: number) => {
    selectWorkspace(wid);
    setStoreMenuOpen(false);
    window.location.reload();
  };


  return (
    <div className="flex h-screen bg-background noise-bg overflow-hidden">
      {/* Onboarding Introduction Tour Modal */}
      <OnboardingTour forceOpen={forceTour} onClose={() => setForceTour(false)} />

      {/* Delete Store Verification Modal */}
      <DeleteStoreModal
        isOpen={!!deleteTargetStore}
        storeId={deleteTargetStore?.id ?? null}
        storeName={deleteTargetStore?.name ?? ''}
        onClose={() => setDeleteTargetStore(null)}
        onSuccess={() => {
          setDeleteTargetStore(null);
          window.location.reload();
        }}
      />

      {/* Add New Store Modal */}
      <AnimatePresence>
        {showAddStoreModal && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 overflow-y-auto">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/80 backdrop-blur-sm"
              onClick={() => { setShowAddStoreModal(false); setStoreError(''); }}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 12 }}
              className="relative w-full max-w-md bg-card border border-border rounded-xl shadow-2xl p-6 z-10 my-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-border">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                    <Store className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground text-sm">Add New Store</h3>
                    <p className="text-xs text-muted-foreground">Create an isolated store workspace</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => { setShowAddStoreModal(false); setStoreError(''); }}
                  className="text-muted-foreground hover:text-foreground p-1 rounded-lg"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {storeError && (
                <div className="mb-4 p-3 rounded-lg bg-destructive/15 text-destructive text-xs">
                  {storeError}
                </div>
              )}

              <form onSubmit={handleCreateStore} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-foreground mb-1 block">Store Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Branch B, Uptown Outlet"
                    value={newStoreName}
                    onChange={(e) => setNewStoreName(e.target.value)}
                    required
                    minLength={2}
                    className="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-foreground mb-1 block">Store Type</label>
                  <select
                    value={newStoreType}
                    onChange={(e) => setNewStoreType(e.target.value)}
                    className="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  >
                    {STORE_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex justify-end gap-2 pt-2 border-t border-border">
                  <button
                    type="button"
                    onClick={() => { setShowAddStoreModal(false); setStoreError(''); }}
                    className="px-3.5 py-2 rounded-lg border border-border bg-card text-foreground text-xs font-medium hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={storeLoading || !newStoreName.trim()}
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
                  >
                    {storeLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                    Create Store
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-card border-r border-border flex flex-col transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 px-5 h-16 border-b border-border">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-data flex items-center justify-center font-bold text-xs text-primary-foreground">
            MM
          </div>
          <span className="font-semibold text-foreground text-sm">Modern Munim</span>
          <button onClick={() => setSidebarOpen(false)} className="ml-auto lg:hidden text-muted-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Current Store Box in Sidebar */}
        <div className="p-3 border-b border-border/80 bg-accent/20">
          <div className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground mb-1 px-1">
            Active Store
          </div>
          <div className="relative">
            <button
              type="button"
              onClick={() => setStoreMenuOpen((o) => !o)}
              className="w-full flex items-center justify-between p-2 rounded-lg bg-card border border-border hover:border-primary/50 text-left transition-colors"
            >
              <div className="flex items-center gap-2 min-w-0">
                <Store className="w-4 h-4 text-primary shrink-0" />
                <div className="truncate">
                  <div className="text-xs font-semibold text-foreground truncate">
                    {activeWorkspace?.name || 'Default Store'}
                  </div>
                  <div className="text-[10px] text-muted-foreground truncate">
                    {activeWorkspace?.store_type || 'Store Workspace'}
                  </div>
                </div>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-muted-foreground shrink-0 ml-1" />
            </button>

            <AnimatePresence>
              {storeMenuOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setStoreMenuOpen(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="absolute left-0 right-0 top-full mt-1.5 p-1 bg-card border border-border rounded-xl shadow-xl z-50 max-h-56 overflow-y-auto"
                  >
                    <div className="text-[10px] font-semibold text-muted-foreground px-2 py-1 uppercase tracking-wider">
                      Switch Store
                    </div>
                    {workspaces.map((ws) => {
                      const isCur = ws.id === activeWorkspace?.id;
                      return (
                        <div
                          key={ws.id}
                          onClick={() => handleSwitchStore(ws.id)}
                          className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer group/store ${
                            isCur ? 'bg-primary/10 text-primary font-medium' : 'text-foreground hover:bg-accent'
                          }`}
                        >
                          <span className="truncate flex-1">{ws.name}</span>
                          <div className="flex items-center gap-1.5 ml-1.5 shrink-0">
                            {isCur && <Check className="w-3.5 h-3.5 text-primary" />}
                            {workspaces.length > 1 && (
                              <button
                                type="button"
                                title={`Delete ${ws.name}`}
                                onClick={(e) => handleDeleteStore(ws.id, ws.name, e)}
                                className="p-1 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors opacity-60 group-hover/store:opacity-100"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}

                    <div className="my-1 border-t border-border" />
                    <button
                      type="button"
                      onClick={() => {
                        setStoreMenuOpen(false);
                        setSidebarOpen(false);
                        setShowAddStoreModal(true);
                      }}
                      className="w-full flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      Add New Store
                    </button>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
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
            onClick={() => setForceTour(true)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent w-full transition-colors"
          >
            <HelpCircle className="w-4 h-4 text-primary" />
            Quick Tour & Intro
          </button>
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
        <header className="relative z-30 h-16 border-b border-border flex items-center px-4 gap-4 bg-card/50 backdrop-blur-sm">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-muted-foreground">
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex-1 min-w-0 flex items-center gap-2">
            <h2 className="text-lg font-semibold text-foreground capitalize truncate">
              {location.pathname.split('/')[1]?.replace('-', ' ') || 'Dashboard'}
            </h2>
            {activeWorkspace && (
              <button
                type="button"
                onClick={() => setShowAddStoreModal(true)}
                className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-medium hover:bg-primary/20 transition-colors"
                title="Current Store Workspace (Click to add or switch)"
              >
                <Store className="w-3 h-3" />
                <span className="max-w-[120px] truncate">{activeWorkspace.name}</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setForceTour(true)}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground text-sm font-medium hover:bg-accent"
              title="Tour & Feature Introduction"
            >
              <HelpCircle className="w-4 h-4 text-primary" />
              <span className="hidden sm:inline">Guide</span>
            </button>
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