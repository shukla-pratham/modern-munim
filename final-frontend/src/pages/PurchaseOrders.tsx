import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { purchaseOrdersAPI, type PurchaseOrderResponse } from '@/lib/api';
import { EMPTY_PO_LIST_MESSAGE, poApiError, poList } from '@/lib/purchaseOrderDisplay';

function formatDate(iso: string | null): string {
  if (!iso) return '';
  try {
    return new Date(iso).toISOString().split('T')[0];
  } catch {
    return iso;
  }
}

function addDays(iso: string, days: number): string {
  const d = new Date(iso);
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

type StepStatus = 'completed' | 'active' | 'pending';

interface TimelineStep {
  id: number;
  label: string;
  status: StepStatus;
  date: string;
}

function buildTimelineSteps(po: PurchaseOrderResponse | null): TimelineStep[] {
  if (!po) return [];
  const orderDate = formatDate(po.order_date);
  const promised = formatDate(po.promised_delivery_date);
  const actual = formatDate(po.actual_delivery_date);
  const status = (po.status || 'created').toLowerCase();
  const isOrdered = status === 'ordered' || status === 'delivered';
  const isDelivered = status === 'delivered';

  const steps: TimelineStep[] = [
    { id: 1, label: 'Requisition Created', status: 'completed', date: orderDate },
    { id: 2, label: 'Manager Approval', status: 'completed', date: orderDate },
    { id: 3, label: 'PO Generated', status: 'completed', date: orderDate },
    { id: 4, label: 'Vendor Confirmed', status: isOrdered ? 'completed' : 'active', date: orderDate ? addDays(orderDate, 2) : '' },
    { id: 5, label: 'Shipped', status: isDelivered ? 'completed' : isOrdered ? 'active' : 'pending', date: promised },
    { id: 6, label: 'Received & QC', status: isDelivered ? 'completed' : 'pending', date: actual },
    { id: 7, label: 'Invoice Matched', status: isDelivered ? 'completed' : 'pending', date: isDelivered ? actual : '' },
    { id: 8, label: 'Payment Released', status: isDelivered ? 'completed' : 'pending', date: isDelivered ? actual : '' },
  ];
  return steps;
}

export default function PurchaseOrders() {
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrderResponse[]>([]);
  const [selectedPoId, setSelectedPoId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    purchaseOrdersAPI
      .list()
      .then((res) => {
        const list = poList(res.data);
        setPurchaseOrders(list);
        if (list.length > 0 && selectedPoId == null) setSelectedPoId(list[0].id);
        else if (list.length > 0 && !list.some((row) => row.id === selectedPoId)) setSelectedPoId(list[0].id);
      })
      .catch((e: unknown) => {
        setError(poApiError(e));
        setPurchaseOrders([]);
      })
      .finally(() => setLoading(false));
  }, []);

  const selectedPo = purchaseOrders.find((po) => po.id === selectedPoId) ?? null;
  const steps = buildTimelineSteps(selectedPo);

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

  return (
    <div className="max-w-4xl mx-auto">
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : purchaseOrders.length === 0 && !error ? (
        <p className="text-muted-foreground text-sm">{EMPTY_PO_LIST_MESSAGE}</p>
      ) : (
        <>
          {/* PO list */}
          {purchaseOrders.length > 1 && (
            <div className="mb-4 flex flex-wrap gap-2">
              {purchaseOrders.map((po) => (
                <button
                  key={po.id}
                  type="button"
                  onClick={() => setSelectedPoId(po.id)}
                  className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                    selectedPoId === po.id
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border bg-card text-foreground hover:bg-accent'
                  }`}
                >
                  #{po.po_number} — {po.vendor_name}
                </button>
              ))}
            </div>
          )}

          {selectedPo && (
            <>
              {/* Header card */}
              <div className="bg-card border border-border rounded-xl p-6 card-shadow mb-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-foreground">Purchase Order #{selectedPo.po_number}</h3>
                  <span className="text-xs text-muted-foreground font-mono">{selectedPo.vendor_name}</span>
                </div>
                <div className="text-sm text-muted-foreground space-y-1">
                  {selectedPo.items.map((item) => (
                    <p key={item.product_id}>
                      {item.product_name} × {item.quantity} units — ₹{Number(item.total_cost).toLocaleString()}
                    </p>
                  ))}
                </div>
              </div>

              {/* Timeline */}
              <motion.div variants={stagger} initial="hidden" animate="show" className="relative">
                <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />

                {steps.map((step, i) => (
                  <motion.div key={step.id} variants={fadeUp} className="relative flex gap-4 mb-2">
                    <div className="relative z-10 flex-shrink-0">
                      {step.status === 'completed' ? (
                        <CheckCircle2 className="w-6 h-6 text-success" />
                      ) : step.status === 'active' ? (
                        <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 2, repeat: Infinity }}>
                          <Circle className="w-6 h-6 text-primary fill-primary/20" />
                        </motion.div>
                      ) : (
                        <Circle className="w-6 h-6 text-muted-foreground/30" />
                      )}
                    </div>

                    <div
                      className={`flex-1 bg-card border rounded-xl p-4 card-shadow cursor-pointer transition-colors ${step.status === 'active' ? 'border-primary/50' : 'border-border'}`}
                      onClick={() => setExpanded(expanded === step.id ? null : step.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className={`text-sm font-medium ${step.status === 'pending' ? 'text-muted-foreground' : 'text-foreground'}`}>
                            {step.label}
                          </p>
                          {step.date && <p className="text-xs text-muted-foreground mt-0.5">{step.date}</p>}
                        </div>
                        {expanded === step.id ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
                      </div>

                      {expanded === step.id && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          className="mt-3 pt-3 border-t border-border text-xs text-muted-foreground"
                        >
                          <p>
                            {step.status === 'completed'
                              ? 'This step has been completed successfully.'
                              : step.status === 'active'
                                ? 'Awaiting action — timeline updates automatically when the PO status or delivery dates change.'
                                : 'This step is pending previous steps.'}
                          </p>
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </>
          )}
        </>
      )}
    </div>
  );
}
