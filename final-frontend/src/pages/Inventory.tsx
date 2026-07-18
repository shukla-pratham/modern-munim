import { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronDown, ChevronUp, X, Plus, Package, Loader2 } from 'lucide-react';
import { productsAPI, inventoryAPI, type ProductResponse } from '@/lib/api';

function StatusBadge({ status }: { status: string }) {
  const styles = {
    'In Stock': 'bg-success/10 text-success border-success/20',
    'Low Stock': 'bg-warning/10 text-warning border-warning/20',
    'Critical': 'bg-critical/10 text-critical border-critical/20',
  }[status] || '';
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${styles}`}>{status}</span>;
}

function getStatus(stock: number, threshold: number): string {
  if (stock <= 0) return 'Critical';
  if (stock <= threshold) return 'Low Stock';
  return 'In Stock';
}

export default function Inventory() {
  const [products, setProducts] = useState<ProductResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<'name' | 'stock_quantity' | 'price' | 'stock_threshold'>('name');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [selectedProduct, setSelectedProduct] = useState<ProductResponse | null>(null);
  const [showAddSku, setShowAddSku] = useState(false);
  const [showAdjustStock, setShowAdjustStock] = useState(false);
  const [adjustProductId, setAdjustProductId] = useState<number | null>(null);

  const fetchProducts = () => {
    setLoading(true);
    setError(null);
    productsAPI
      .list()
      .then((res) => setProducts(res.data ?? []))
      .catch((err) => setError(err.response?.data?.detail ?? err.message ?? 'Failed to load products'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchProducts(); }, []);

  const filtered = useMemo(() => {
    let items = products.filter(
      (p) =>
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        (p.description ?? '').toLowerCase().includes(search.toLowerCase())
    );
    items = [...items].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const cmp = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv));
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return items;
  }, [products, search, sortKey, sortDir]);

  const handleSort = (key: typeof sortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const SortIcon = ({ col }: { col: typeof sortKey }) =>
    sortKey === col ? (sortDir === 'asc' ? <ChevronUp className="w-3 h-3 inline ml-1" /> : <ChevronDown className="w-3 h-3 inline ml-1" />) : null;

  return (
    <div>
      {/* Header + actions */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by name or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-card border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
        <span className="text-sm text-muted-foreground">{filtered.length} SKUs</span>
        <button
          type="button"
          onClick={() => setShowAddSku(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90"
        >
          <Plus className="w-4 h-4" />
          Add SKU
        </button>
        <button
          type="button"
          onClick={() => { setAdjustProductId(null); setShowAdjustStock(true); }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-card text-foreground text-sm font-medium hover:bg-accent"
        >
          <Package className="w-4 h-4" />
          Adjust stock
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="bg-card border border-border rounded-xl card-shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th onClick={() => handleSort('name')} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground cursor-pointer hover:text-foreground">
                    Name <SortIcon col="name" />
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Description</th>
                  <th onClick={() => handleSort('stock_quantity')} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground cursor-pointer hover:text-foreground">
                    Stock <SortIcon col="stock_quantity" />
                  </th>
                  <th onClick={() => handleSort('stock_threshold')} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground cursor-pointer hover:text-foreground">
                    Threshold <SortIcon col="stock_threshold" />
                  </th>
                  <th onClick={() => handleSort('price')} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground cursor-pointer hover:text-foreground">
                    Price <SortIcon col="price" />
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((p) => (
                  <tr
                    key={p.id}
                    className="border-b border-border/50 hover:bg-accent/50 cursor-pointer"
                    onClick={() => setSelectedProduct(p)}
                  >
                    <td className="px-4 py-3 font-medium text-foreground">{p.name}</td>
                    <td className="px-4 py-3 text-muted-foreground max-w-[200px] truncate">{p.description ?? '—'}</td>
                    <td className="px-4 py-3 text-foreground">{p.stock_quantity}</td>
                    <td className="px-4 py-3 text-foreground">{p.stock_threshold}</td>
                    <td className="px-4 py-3 text-foreground">₹{Number(p.price).toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={getStatus(p.stock_quantity, p.stock_threshold)} />
                    </td>
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <button
                        type="button"
                        onClick={() => { setAdjustProductId(p.id); setShowAdjustStock(true); }}
                        className="text-xs text-primary hover:underline"
                      >
                        Adjust stock
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && (
            <div className="py-12 text-center text-muted-foreground text-sm">No products. Add a SKU to get started.</div>
          )}
        </div>
      )}

      {/* Add SKU modal */}
      <AnimatePresence>
        {showAddSku && (
          <AddSkuModal
            onClose={() => setShowAddSku(false)}
            onSuccess={() => { setShowAddSku(false); fetchProducts(); }}
          />
        )}
      </AnimatePresence>

      {/* Adjust stock modal */}
      <AnimatePresence>
        {showAdjustStock && (
          <AdjustStockModal
            products={products}
            preselectedProductId={adjustProductId}
            onClose={() => { setShowAdjustStock(false); setAdjustProductId(null); }}
            onSuccess={() => { setShowAdjustStock(false); setAdjustProductId(null); fetchProducts(); }}
          />
        )}
      </AnimatePresence>

      {/* Detail side panel */}
      <AnimatePresence>
        {selectedProduct && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/60 backdrop-blur-sm z-40"
              onClick={() => setSelectedProduct(null)}
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-card border-l border-border z-50 overflow-y-auto"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-semibold text-foreground">{selectedProduct.name}</h3>
                  <button onClick={() => setSelectedProduct(null)} className="text-muted-foreground hover:text-foreground">
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-secondary rounded-lg p-3">
                    <p className="text-xs text-muted-foreground">ID</p>
                    <p className="font-mono text-sm text-foreground">{selectedProduct.id}</p>
                  </div>
                  <div className="bg-secondary rounded-lg p-3">
                    <p className="text-xs text-muted-foreground">Stock</p>
                    <p className="text-sm text-foreground font-semibold">{selectedProduct.stock_quantity}</p>
                  </div>
                  <div className="bg-secondary rounded-lg p-3">
                    <p className="text-xs text-muted-foreground">Threshold</p>
                    <p className="text-sm text-foreground">{selectedProduct.stock_threshold}</p>
                  </div>
                  <div className="bg-secondary rounded-lg p-3">
                    <p className="text-xs text-muted-foreground">Price</p>
                    <p className="text-sm text-foreground">₹{Number(selectedProduct.price).toLocaleString()}</p>
                  </div>
                </div>
                {selectedProduct.description && (
                  <p className="mt-4 text-sm text-muted-foreground">{selectedProduct.description}</p>
                )}
                <button
                  type="button"
                  onClick={() => { setAdjustProductId(selectedProduct.id); setSelectedProduct(null); setShowAdjustStock(true); }}
                  className="mt-6 w-full py-2 rounded-lg border border-border bg-card text-foreground text-sm font-medium hover:bg-accent"
                >
                  Adjust stock
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

function AddSkuModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [stock_quantity, setStockQuantity] = useState('0');
  const [stock_threshold, setStockThreshold] = useState('10');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    const numPrice = parseFloat(price);
    const numStock = parseInt(stock_quantity, 10);
    const numThreshold = parseInt(stock_threshold, 10);
    if (!name.trim()) { setErr('Name is required'); return; }
    if (isNaN(numPrice) || numPrice < 0) { setErr('Valid price required'); return; }
    if (isNaN(numStock) || numStock < 0) { setErr('Stock must be ≥ 0'); return; }
    if (isNaN(numThreshold) || numThreshold < 0) { setErr('Threshold must be ≥ 0'); return; }
    setSubmitting(true);
    productsAPI
      .create({
        name: name.trim(),
        description: description.trim() || undefined,
        price: numPrice,
        stock_quantity: numStock,
        stock_threshold: numThreshold,
      })
      .then(() => onSuccess())
      .catch((e) => setErr(e.response?.data?.detail ?? e.message ?? 'Failed to create'))
      .finally(() => setSubmitting(false));
  };

  return (
    <>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-background/60 backdrop-blur-sm z-50" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-card border border-border rounded-xl shadow-xl z-50 p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-foreground">Add SKU / Product</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Name *</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" required />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Price *</label>
              <input type="number" step="0.01" min="0" value={price} onChange={(e) => setPrice(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Initial stock</label>
              <input type="number" min="0" value={stock_quantity} onChange={(e) => setStockQuantity(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Low-stock threshold</label>
            <input type="number" min="0" value={stock_threshold} onChange={(e) => setStockThreshold(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
          </div>
          {err && <p className="text-sm text-destructive">{err}</p>}
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-border text-foreground text-sm font-medium">Cancel</button>
            <button type="submit" disabled={submitting} className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin inline" /> : 'Add SKU'}
            </button>
          </div>
        </form>
      </motion.div>
    </>
  );
}

function AdjustStockModal({
  products,
  preselectedProductId,
  onClose,
  onSuccess,
}: {
  products: ProductResponse[];
  preselectedProductId: number | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [productId, setProductId] = useState<number | ''>(preselectedProductId ?? '');
  const [quantity, setQuantity] = useState('1');
  const [type, setType] = useState<'in' | 'out'>('in');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { if (preselectedProductId) setProductId(preselectedProductId); }, [preselectedProductId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    const pid = typeof productId === 'number' ? productId : parseInt(String(productId), 10);
    const qty = parseInt(quantity, 10);
    if (!pid || isNaN(pid)) { setErr('Select a product'); return; }
    if (isNaN(qty) || qty < 1) { setErr('Quantity must be ≥ 1'); return; }
    setSubmitting(true);
    const req = type === 'in' ? inventoryAPI.stockIn(pid, qty, reason || undefined) : inventoryAPI.stockOut(pid, qty, reason || undefined);
    req
      .then(() => onSuccess())
      .catch((e) => setErr(e.response?.data?.detail ?? e.message ?? 'Failed'))
      .finally(() => setSubmitting(false));
  };

  return (
    <>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-background/60 backdrop-blur-sm z-50" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-card border border-border rounded-xl shadow-xl z-50 p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-foreground">Adjust stock</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Product</label>
            <select
              value={productId}
              onChange={(e) => setProductId(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm"
            >
              <option value="">Select product</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>{p.name} (stock: {p.stock_quantity})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Type</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="type" checked={type === 'in'} onChange={() => setType('in')} />
                <span className="text-sm">Stock In</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="type" checked={type === 'out'} onChange={() => setType('out')} />
                <span className="text-sm">Stock Out</span>
              </label>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Quantity *</label>
            <input type="number" min="1" value={quantity} onChange={(e) => setQuantity(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Reason (optional)</label>
            <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder={type === 'in' ? 'e.g. Manual restock' : 'e.g. Sale'} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
          </div>
          {err && <p className="text-sm text-destructive">{err}</p>}
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-border text-foreground text-sm font-medium">Cancel</button>
            <button type="submit" disabled={submitting} className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin inline" /> : 'Apply'}
            </button>
          </div>
        </form>
      </motion.div>
    </>
  );
}
