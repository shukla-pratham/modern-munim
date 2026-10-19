import { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowUpDown, Package, ShoppingCart, Loader2, Plus, Trash2 } from 'lucide-react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip,
} from 'recharts';
import { vendorsAPI, purchaseOrdersAPI, vendorsCreateAPI, productsAPI, API_URL, type VendorRanking, type VendorProduct } from '@/lib/api';

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, value)}%` }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className={`h-full rounded-full ${color}`}
      />
    </div>
  );
}

function ComparisonPanel({
  vendors,
  onClose,
}: {
  vendors: VendorRanking[];
  onClose: () => void;
}) {
  const [a, b] = vendors;
  // Lead time: lower days = better; convert to 0–100 score (shorter = higher score)
  const leadScore = (days: number | null) =>
    Math.max(0, Math.min(100, 100 - (days ?? 0) * 5));
  const radarData = [
    { metric: 'Reliability', short: 'Reliab.', A: a.reliability_score ?? 0, B: b.reliability_score ?? 0 },
    { metric: 'Cost', short: 'Cost', A: a.cost_score ?? 0, B: b.cost_score ?? 0 },
    { metric: 'Overall', short: 'Overall', A: a.overall_score ?? 0, B: b.overall_score ?? 0 },
    { metric: 'Lead time', short: 'Lead', A: leadScore(a.avg_lead_time_days), B: leadScore(b.avg_lead_time_days) },
  ];

  const tickStyle = { fontSize: 11, fill: 'hsl(var(--foreground))' };
  const radarMargin = { top: 24, right: 36, bottom: 24, left: 36 };

  const formatScore = (v: number | null) => (v != null ? Number(v).toFixed(1) : '—');
  const explanationA = a.explanation ?? 'No details available';
  const explanationB = b.explanation ?? 'No details available';

  return (
    <motion.div
      initial={{ y: '100%' }}
      animate={{ y: 0 }}
      exit={{ y: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed bottom-0 right-0 left-0 lg:left-64 z-50 bg-card border-t border-border shadow-lg rounded-t-2xl max-h-[75vh] overflow-y-auto"
    >
      <div className="p-4 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-foreground">Vendor Comparison</h3>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted"
            aria-label="Close comparison"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 min-w-0">
          {/* Radar chart – ensure container has size */}
          <div className="min-w-0 min-h-[240px] flex flex-col">
            <div className="flex-1 min-h-[220px] w-full">
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData} margin={radarMargin}>
                  <PolarGrid stroke="hsl(var(--border))" />
                  <PolarAngleAxis dataKey="short" tick={tickStyle} />
                  <PolarRadiusAxis domain={[0, 100]} tick={tickStyle} />
                  <Radar name={a.vendor_name} dataKey="A" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.25} strokeWidth={1.5} />
                  <Radar name={b.vendor_name} dataKey="B" stroke="hsl(var(--data))" fill="hsl(var(--data))" fillOpacity={0.25} strokeWidth={1.5} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs mt-2 flex-shrink-0">
              <span className="flex items-center gap-1.5 min-w-0" title={a.vendor_name}>
                <span className="w-3 h-3 rounded-full bg-primary shrink-0" aria-hidden />
                <span className="truncate max-w-[140px]">{a.vendor_name}</span>
              </span>
              <span className="flex items-center gap-1.5 min-w-0" title={b.vendor_name}>
                <span className="w-3 h-3 rounded-full bg-data shrink-0" aria-hidden />
                <span className="truncate max-w-[140px]">{b.vendor_name}</span>
              </span>
            </div>
          </div>
          {/* Score bars – match radar colors: first vendor primary, second data */}
          <div className="space-y-4 min-w-0">
            <h4 className="text-sm font-medium text-foreground">Overall Score</h4>
            {[a, b].map((v, i) => (
              <div key={v.vendor_id} className="space-y-1.5">
                <div className="flex justify-between text-xs gap-2">
                  <span className="text-muted-foreground truncate min-w-0">{v.vendor_name}</span>
                  <span className="text-foreground font-semibold shrink-0">{formatScore(v.overall_score)}</span>
                </div>
                <ScoreBar value={Number(v.overall_score) ?? 0} color={i === 0 ? 'bg-primary' : 'bg-data'} />
              </div>
            ))}
            <h4 className="text-sm font-medium text-foreground mt-4">Reliability</h4>
            {[a, b].map((v, i) => (
              <div key={`rel-${v.vendor_id}`} className="space-y-1.5">
                <div className="flex justify-between text-xs gap-2">
                  <span className="text-muted-foreground truncate min-w-0">{v.vendor_name}</span>
                  <span className="text-foreground font-semibold shrink-0">{formatScore(v.reliability_score)}</span>
                </div>
                <ScoreBar value={Number(v.reliability_score) ?? 0} color={i === 0 ? 'bg-primary' : 'bg-data'} />
              </div>
            ))}
          </div>
          {/* Details */}
          <div className="space-y-3 min-w-0">
            <h4 className="text-sm font-medium text-foreground">Details</h4>
            <div className="space-y-3 max-h-[200px] overflow-y-auto pr-1">
              <div>
                <p className="text-xs font-medium text-foreground mb-0.5 truncate" title={a.vendor_name}>{a.vendor_name}</p>
                <p className="text-xs text-muted-foreground whitespace-pre-wrap break-words">{explanationA}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-foreground mb-0.5 truncate" title={b.vendor_name}>{b.vendor_name}</p>
                <p className="text-xs text-muted-foreground whitespace-pre-wrap break-words">{explanationB}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function Vendors() {
  const [vendors, setVendors] = useState<VendorRanking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<number[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [selectedVendorId, setSelectedVendorId] = useState<number | null>(null);
  const [vendorProducts, setVendorProducts] = useState<VendorProduct[]>([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [orderQuantities, setOrderQuantities] = useState<Record<number, number>>({});
  const [placing, setPlacing] = useState(false);
  const [placeOrderError, setPlaceOrderError] = useState<string | null>(null);
  const [orderSuccess, setOrderSuccess] = useState<string | null>(null);
  const [showAddVendor, setShowAddVendor] = useState(false);
  const [showAddProductToVendor, setShowAddProductToVendor] = useState(false);
  const [vendorToDelete, setVendorToDelete] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const fetchVendors = () => {
    setLoading(true);
    setError(null);
    vendorsAPI
      .rankings()
      .then((res) => {
        setVendors(res.data ?? []);
      })
      .catch((err) => {
        const noResponse = !err.response;
        const data = err.response?.data;
        const msg = noResponse
          ? `Could not reach the API. Is the backend running at ${API_URL}?`
          : (Array.isArray(data?.detail)
            ? data.detail.map((x: { msg?: string }) => x.msg ?? '').join('. ')
            : data?.detail ?? data?.error ?? err.message) ?? 'Failed to load vendors';
        setError(msg);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchVendors();
  }, []);

  useEffect(() => {
    if (selectedVendorId == null) {
      setVendorProducts([]);
      setOrderQuantities({});
      return;
    }
    setProductsLoading(true);
    vendorsAPI
      .vendorProducts(selectedVendorId)
      .then((res) => {
        const list = res.data ?? [];
        setVendorProducts(list);
        const qty: Record<number, number> = {};
        list.forEach((p) => { qty[p.product_id] = p.min_order_qty; });
        setOrderQuantities(qty);
      })
      .catch(() => setVendorProducts([]))
      .finally(() => setProductsLoading(false));
  }, [selectedVendorId]);

  const toggleCompare = (id: number) => {
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  };

  const compareVendors = useMemo(
    () => vendors.filter((v) => compareIds.includes(v.vendor_id)),
    [vendors, compareIds]
  );

  const selectedVendor = useMemo(
    () => vendors.find((v) => v.vendor_id === selectedVendorId),
    [vendors, selectedVendorId]
  );

  const handlePlaceOrder = () => {
    if (!selectedVendorId) return;
    const items = vendorProducts
      .filter((p) => (orderQuantities[p.product_id] ?? 0) >= p.min_order_qty)
      .map((p) => ({
        product_id: p.product_id,
        quantity: orderQuantities[p.product_id] ?? p.min_order_qty,
        unit_cost: p.unit_cost,
      }));
    if (items.length === 0) {
      setPlaceOrderError('Add at least one item with quantity ≥ min order qty.');
      return;
    }
    setPlacing(true);
    setPlaceOrderError(null);
    setOrderSuccess(null);
    purchaseOrdersAPI
      .create({ vendor_id: selectedVendorId, items })
      .then((res) => {
        setOrderSuccess(`Order ${res.data.po_number} placed. Total: ₹${res.data.total_cost.toFixed(2)}`);
        setOrderQuantities((prev) => {
          const next = { ...prev };
          vendorProducts.forEach((p) => { next[p.product_id] = p.min_order_qty; });
          return next;
        });
      })
      .catch((err) => {
        const d = err.response?.data?.detail;
        setPlaceOrderError(Array.isArray(d) ? d.map((x: { msg?: string }) => x.msg ?? '').join('. ') : typeof d === 'string' ? d : 'Failed to place order');
      })
      .finally(() => setPlacing(false));
  };

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

  return (
    <div>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <p className="text-sm text-muted-foreground">
          {loading ? 'Loading…' : `${vendors.length} vendors`}
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowAddVendor(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90"
          >
            <Plus className="w-4 h-4" />
            Add vendor
          </button>
          <button
            onClick={() => setShowComparison(true)}
            disabled={compareIds.length !== 2}
            className="px-4 py-2 bg-primary/20 text-primary rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/30 transition-opacity inline-flex items-center gap-2"
          >
            <ArrowUpDown className="w-4 h-4" />
            Compare ({compareIds.length}/2)
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex flex-wrap items-center gap-2">
          <span className="flex-1">{error}</span>
          <button
            type="button"
            onClick={() => fetchVendors()}
            className="px-3 py-1.5 rounded-md bg-destructive/20 text-destructive font-medium hover:bg-destructive/30 text-sm"
          >
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
        >
          {vendors.map((vendor) => (
            <motion.div
              key={vendor.vendor_id}
              variants={fadeUp}
              className={`bg-card border rounded-xl p-4 card-shadow hover:card-shadow-hover transition-all cursor-pointer ${
                compareIds.includes(vendor.vendor_id) ? 'border-primary ring-1 ring-primary/30' : 'border-border'
              }`}
              onClick={() => toggleCompare(vendor.vendor_id)}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-foreground text-sm">{vendor.vendor_name}</h3>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setVendorToDelete(vendor.vendor_id); setDeleteError(null); }}
                  className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                  title="Delete vendor"
                  aria-label="Delete vendor"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="flex items-end gap-2 mb-3">
                <span className="text-3xl font-bold text-foreground">
                  {vendor.overall_score ?? '—'}
                </span>
                <span className="text-xs text-muted-foreground mb-1">/100</span>
              </div>
              <div className="space-y-2 mb-3">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Reliability</span>
                    <span className="text-foreground">{vendor.reliability_score ?? '—'}%</span>
                  </div>
                  <ScoreBar value={vendor.reliability_score ?? 0} color="bg-primary" />
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Cost score</span>
                    <span className="text-foreground">{vendor.cost_score ?? '—'}%</span>
                  </div>
                  <ScoreBar value={vendor.cost_score ?? 0} color="bg-data" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{vendor.explanation}</p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedVendorId(vendor.vendor_id);
                }}
                className="w-full mt-2 px-3 py-2 rounded-lg bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 flex items-center justify-center gap-2"
              >
                <Package className="w-4 h-4" />
                Inventory & place order
              </button>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Vendor detail: Inventory & Place order */}
      <AnimatePresence>
        {selectedVendorId != null && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/60 backdrop-blur-sm z-40"
              onClick={() => { setSelectedVendorId(null); setOrderSuccess(null); setPlaceOrderError(null); }}
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 bottom-0 w-full max-w-lg z-50 bg-card border-l border-border shadow-xl overflow-y-auto"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-foreground">
                    {selectedVendor?.vendor_name ?? 'Vendor'} — Inventory & order
                  </h2>
                  <button
                    onClick={() => { setSelectedVendorId(null); setOrderSuccess(null); setPlaceOrderError(null); }}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {productsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                  </div>
                ) : vendorProducts.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No products from this vendor.</p>
                ) : (
                  <>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
                        <Package className="w-4 h-4" />
                        Products (inventory)
                      </h3>
                      <button
                        type="button"
                        onClick={() => setShowAddProductToVendor(true)}
                        className="text-xs px-2 py-1 rounded border border-border bg-card text-foreground hover:bg-accent"
                      >
                        Add product to vendor
                      </button>
                    </div>
                    <div className="rounded-lg border border-border overflow-hidden mb-6">
                      <table className="w-full text-sm">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="text-left p-2 font-medium">Product</th>
                            <th className="text-right p-2 font-medium">Unit cost</th>
                            <th className="text-right p-2 font-medium">Min qty</th>
                            <th className="text-right p-2 font-medium">Lead days</th>
                          </tr>
                        </thead>
                        <tbody>
                          {vendorProducts.map((p) => (
                            <tr key={p.product_id} className="border-t border-border">
                              <td className="p-2 text-foreground">{p.product_name}</td>
                              <td className="p-2 text-right text-muted-foreground">₹{p.unit_cost.toFixed(2)}</td>
                              <td className="p-2 text-right text-muted-foreground">{p.min_order_qty}</td>
                              <td className="p-2 text-right text-muted-foreground">{p.lead_time_days ?? '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <h3 className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                      <ShoppingCart className="w-4 h-4" />
                      Place order
                    </h3>
                    <p className="text-xs text-muted-foreground mb-3">
                      Set quantity for each product (must be ≥ min order qty). Then submit.
                    </p>
                    <div className="space-y-3 mb-4">
                      {vendorProducts.map((p) => (
                        <div key={p.product_id} className="flex items-center gap-3">
                          <label className="flex-1 text-sm text-foreground">{p.product_name}</label>
                          <input
                            type="number"
                            min={p.min_order_qty}
                            value={orderQuantities[p.product_id] ?? p.min_order_qty}
                            onChange={(e) =>
                              setOrderQuantities((prev) => ({
                                ...prev,
                                [p.product_id]: Math.max(p.min_order_qty, parseInt(e.target.value, 10) || p.min_order_qty),
                              }))
                            }
                            className="w-20 rounded border border-border bg-background px-2 py-1.5 text-sm"
                          />
                          <span className="text-xs text-muted-foreground">min {p.min_order_qty}</span>
                        </div>
                      ))}
                    </div>
                    {placeOrderError && (
                      <p className="text-sm text-destructive mb-2">{placeOrderError}</p>
                    )}
                    {orderSuccess && (
                      <p className="text-sm text-green-600 dark:text-green-400 mb-2">{orderSuccess}</p>
                    )}
                    <button
                      onClick={handlePlaceOrder}
                      disabled={placing}
                      className="w-full py-2.5 rounded-lg bg-primary text-primary-foreground font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {placing ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShoppingCart className="w-4 h-4" />}
                      {placing ? 'Placing order…' : 'Submit order'}
                    </button>
                  </>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Comparison panel */}
      <AnimatePresence>
        {showComparison && compareIds.length === 2 && compareVendors.length === 2 && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/60 backdrop-blur-sm z-40"
              onClick={() => setShowComparison(false)}
            />
            <ComparisonPanel vendors={compareVendors} onClose={() => setShowComparison(false)} />
          </>
        )}
      </AnimatePresence>

      {/* Add vendor modal */}
      <AnimatePresence>
        {showAddVendor && (
          <AddVendorModal
            onClose={() => setShowAddVendor(false)}
            onSuccess={() => { setShowAddVendor(false); fetchVendors(); }}
          />
        )}
      </AnimatePresence>

      {/* Add product to vendor modal */}
      <AnimatePresence>
        {showAddProductToVendor && selectedVendorId != null && (
          <AddProductToVendorModal
            vendorId={selectedVendorId}
            vendorName={selectedVendor?.vendor_name ?? 'Vendor'}
            onClose={() => setShowAddProductToVendor(false)}
            onSuccess={() => { setShowAddProductToVendor(false); vendorsAPI.vendorProducts(selectedVendorId).then((r) => setVendorProducts(r.data ?? [])); }}
          />
        )}
      </AnimatePresence>

      {/* Delete vendor confirmation */}
      <AnimatePresence>
        {vendorToDelete != null && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/60 backdrop-blur-sm z-50"
              onClick={() => { setVendorToDelete(null); setDeleteError(null); }}
            />
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full max-w-sm bg-card border border-border rounded-xl shadow-xl p-6 pointer-events-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 className="font-semibold text-foreground mb-1">Delete vendor</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Delete <strong>{vendors.find((v) => v.vendor_id === vendorToDelete)?.vendor_name ?? 'this vendor'}</strong>? This cannot be undone. Vendors with existing purchase orders cannot be deleted.
                </p>
                {deleteError && (
                  <p className="text-sm text-destructive mb-3">{deleteError}</p>
                )}
                <div className="flex gap-3 justify-end">
                  <button
                    type="button"
                    onClick={() => { setVendorToDelete(null); setDeleteError(null); }}
                    className="px-4 py-2 rounded-lg border border-border bg-card text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={async () => {
                      if (vendorToDelete == null) return;
                      setDeleting(true);
                      setDeleteError(null);
                      try {
                        await vendorsAPI.delete(vendorToDelete);
                        setVendorToDelete(null);
                        if (selectedVendorId === vendorToDelete) setSelectedVendorId(null);
                        fetchVendors();
                      } catch (e: unknown) {
                        const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to delete vendor.';
                        setDeleteError(msg);
                      } finally {
                        setDeleting(false);
                      }
                    }}
                    disabled={deleting}
                    className="px-4 py-2 rounded-lg bg-destructive text-destructive-foreground font-medium hover:bg-destructive/90 disabled:opacity-50 flex items-center gap-2"
                  >
                    {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                    {deleting ? 'Deleting…' : 'Delete'}
                  </button>
                </div>
              </motion.div>
            </div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

function AddVendorModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [name, setName] = useState('');
  const [avg_lead_time_days, setAvgLeadTimeDays] = useState('');
  const [reliability_score, setReliabilityScore] = useState('');
  const [cost_score, setCostScore] = useState('');
  const [overall_score, setOverallScore] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    if (!name.trim()) { setErr('Name is required'); return; }
    setSubmitting(true);
    vendorsCreateAPI
      .create({
        name: name.trim(),
        avg_lead_time_days: avg_lead_time_days ? parseInt(avg_lead_time_days, 10) : undefined,
        reliability_score: reliability_score ? parseFloat(reliability_score) : undefined,
        cost_score: cost_score ? parseFloat(cost_score) : undefined,
        overall_score: overall_score ? parseFloat(overall_score) : undefined,
      })
      .then(() => onSuccess())
      .catch((e) => setErr(e.response?.data?.detail ?? e.message ?? 'Failed to create vendor'))
      .finally(() => setSubmitting(false));
  };

  return (
    <>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-background/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto pointer-events-none">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full max-w-md max-h-[90vh] overflow-y-auto bg-card border border-border rounded-xl shadow-2xl p-6 pointer-events-auto my-auto"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-foreground">Add vendor</h3>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-5 h-5" /></button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Name *</label>
              <input value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Avg lead time (days)</label>
              <input type="number" min="0" value={avg_lead_time_days} onChange={(e) => setAvgLeadTimeDays(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Reliability (0–100)</label>
                <input type="number" min="0" max="100" step="0.1" value={reliability_score} onChange={(e) => setReliabilityScore(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Cost score (0–100)</label>
                <input type="number" min="0" max="100" step="0.1" value={cost_score} onChange={(e) => setCostScore(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Overall score (0–100)</label>
              <input type="number" min="0" max="100" step="0.1" value={overall_score} onChange={(e) => setOverallScore(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
            </div>
            {err && <p className="text-sm text-destructive">{err}</p>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-border text-foreground text-sm font-medium hover:bg-accent">Cancel</button>
              <button type="submit" disabled={submitting} className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 disabled:opacity-50">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin inline" /> : 'Add vendor'}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </>
  );
}

function AddProductToVendorModal({
  vendorId,
  vendorName,
  onClose,
  onSuccess,
}: {
  vendorId: number;
  vendorName: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [products, setProducts] = useState<{ id: number; name: string; price: number }[]>([]);
  const [productId, setProductId] = useState<number | ''>('');
  const [unit_cost, setUnitCost] = useState('');
  const [min_order_qty, setMinOrderQty] = useState('1');
  const [lead_time_days, setLeadTimeDays] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    productsAPI.list().then((r) => setProducts(r.data ?? []));
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    const pid = typeof productId === 'number' ? productId : parseInt(String(productId), 10);
    const cost = parseFloat(unit_cost);
    const minQty = parseInt(min_order_qty, 10);
    if (!pid || isNaN(pid)) { setErr('Select a product'); return; }
    if (isNaN(cost) || cost < 0) { setErr('Valid unit cost required'); return; }
    if (isNaN(minQty) || minQty < 1) { setErr('Min order qty must be ≥ 1'); return; }
    setSubmitting(true);
    vendorsCreateAPI
      .addProduct(vendorId, {
        product_id: pid,
        unit_cost: cost,
        min_order_qty: minQty,
        lead_time_days: lead_time_days ? parseInt(lead_time_days, 10) : undefined,
      })
      .then(() => onSuccess())
      .catch((e) => setErr(e.response?.data?.detail ?? e.message ?? 'Failed'))
      .finally(() => setSubmitting(false));
  };

  return (
    <>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-background/60 backdrop-blur-sm z-50" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto pointer-events-none">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full max-w-md max-h-[90vh] overflow-y-auto bg-card border border-border rounded-xl shadow-2xl p-6 pointer-events-auto my-auto"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-foreground">Add product to {vendorName}</h3>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-5 h-5" /></button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Product *</label>
              <select
                value={productId}
                onChange={(e) => setProductId(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm"
              >
                <option value="">Select product</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} (₹{Number(p.price).toLocaleString()})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Unit cost (₹) *</label>
              <input type="number" step="0.01" min="0" value={unit_cost} onChange={(e) => setUnitCost(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Min order qty *</label>
                <input type="number" min="1" value={min_order_qty} onChange={(e) => setMinOrderQty(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Lead time (days)</label>
                <input type="number" min="0" value={lead_time_days} onChange={(e) => setLeadTimeDays(e.target.value)} className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm" />
              </div>
            </div>
            {err && <p className="text-sm text-destructive">{err}</p>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-border text-foreground text-sm font-medium hover:bg-accent">Cancel</button>
              <button type="submit" disabled={submitting} className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 disabled:opacity-50">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin inline" /> : 'Add product'}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </>
  );
}
