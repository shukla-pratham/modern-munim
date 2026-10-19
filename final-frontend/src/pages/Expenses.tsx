import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Loader2, Pencil, Plus, Trash2, X } from 'lucide-react';
import { expensesAPI, type ExpenseResponse } from '@/lib/api';
import {
  EXPENSE_CATEGORY_ORDER,
  EXPENSE_TYPE_ORDER,
  buildExpenseCreatePayload,
  buildExpenseUpdatePayload,
  categoryLabel,
  expenseApiError,
  toNumber,
  totalsByCategory,
  typeLabel,
  type ExpenseFormFields,
} from '@/lib/expenseDisplay';

function formatMoney(value: number): string {
  return `₹${toNumber(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().slice(0, 10);
}

function emptyForm(): ExpenseFormFields {
  return {
    category: 'operations',
    description: '',
    amount: '',
    expenseType: 'one_time',
    productId: '',
  };
}

function formFromExpense(e: ExpenseResponse): ExpenseFormFields {
  return {
    category: e.category,
    description: e.description,
    amount: String(e.amount ?? ''),
    expenseType: e.expense_type || 'one_time',
    productId: e.product_id != null ? String(e.product_id) : '',
  };
}

function categoryFromSearch(raw: string | null): string | null {
  if (!raw) return null;
  const key = raw.trim().toLowerCase();
  return (EXPENSE_CATEGORY_ORDER as readonly string[]).includes(key) ? key : null;
}

export default function Expenses() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(() =>
    categoryFromSearch(searchParams.get('category'))
  );
  const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<ExpenseResponse | null>(null);
  const [expenseToDelete, setExpenseToDelete] = useState<ExpenseResponse | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    setSelectedCategory(categoryFromSearch(searchParams.get('category')));
  }, [searchParams]);

  const selectCategory = (key: string | null) => {
    setSelectedCategory(key);
    if (key) setSearchParams({ category: key }, { replace: true });
    else setSearchParams({}, { replace: true });
  };

  const fetchExpenses = useCallback(() => {
    setLoading(true);
    setError(null);
    return expensesAPI
      .list({
        limit: 100,
        ...(selectedCategory ? { category: selectedCategory } : {}),
      })
      .then((res) => {
        setExpenses(res.data ?? []);
      })
      .catch((err) => {
        setExpenses([]);
        setError(expenseApiError(err));
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedCategory]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    expensesAPI
      .list({
        limit: 100,
        ...(selectedCategory ? { category: selectedCategory } : {}),
      })
      .then((res) => {
        if (!cancelled) setExpenses(res.data ?? []);
      })
      .catch((err) => {
        if (!cancelled) {
          setExpenses([]);
          setError(expenseApiError(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [selectedCategory]);

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };
  const categoryTotals = totalsByCategory(expenses);
  const spendTotal = categoryTotals.reduce((sum, c) => sum + c.actual, 0);
  const chartData = selectedCategory
    ? categoryTotals.filter((c) => c.key === selectedCategory)
    : categoryTotals;

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => selectCategory(null)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${!selectedCategory ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
        >
          All
        </button>
        {EXPENSE_CATEGORY_ORDER.map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => selectCategory(key === selectedCategory ? null : key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${selectedCategory === key ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
          >
            {categoryLabel(key)}
          </button>
        ))}
        <button
          type="button"
          onClick={() => { setEditing(null); setShowForm(true); setNotice(null); }}
          className="ml-auto px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-medium flex items-center gap-1"
        >
          <Plus className="w-3.5 h-3.5" /> Add expense
        </button>
      </motion.div>

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}
      {notice && (
        <div className="p-3 rounded-lg bg-secondary text-foreground text-sm">{notice}</div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
            <h3 className="font-semibold text-foreground text-sm mb-4">Spend by Category</h3>
            {expenses.length === 0 ? (
              <div className="h-[300px] flex items-center justify-center text-sm text-muted-foreground">
                No expenses
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
                  <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
                  <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: 12 }} />
                  <Bar dataKey="actual" radius={[4, 4, 0, 0]} name="Actual">
                    {chartData.map((entry) => (
                      <Cell key={entry.key} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </motion.div>

          <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {categoryTotals.map((d) => (
              <div key={d.key} className="bg-card border border-border rounded-xl p-4 card-shadow hover:card-shadow-hover transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-foreground">{d.name}</h4>
                  <span className="text-xs font-medium text-muted-foreground">{d.count} items</span>
                </div>
                <div className="space-y-1 text-xs text-muted-foreground">
                  <div className="flex justify-between">
                    <span>Spend</span>
                    <span className="text-foreground">{formatMoney(d.actual)}</span>
                  </div>
                </div>
                <div className="mt-3 h-1.5 bg-secondary rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${spendTotal > 0 ? Math.min(100, (d.actual / spendTotal) * 100) : 0}%` }}
                    transition={{ duration: 0.8 }}
                    className="h-full rounded-full bg-primary"
                    style={{ background: d.color }}
                  />
                </div>
              </div>
            ))}
          </motion.div>

          <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl card-shadow overflow-hidden">
            <div className="px-4 py-3 border-b border-border">
              <h3 className="font-semibold text-foreground text-sm">Expenses</h3>
            </div>
            {expenses.length === 0 ? (
              <div className="py-12 text-center text-sm text-muted-foreground">No expenses</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Description</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Category</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Type</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Amount</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Product</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Date</th>
                      <th className="text-right px-4 py-3 text-xs font-medium text-muted-foreground">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expenses.map((e) => (
                      <tr key={e.id} className="border-b border-border/50 hover:bg-accent/50">
                        <td className="px-4 py-3 text-foreground">{e.description}</td>
                        <td className="px-4 py-3 text-muted-foreground">{categoryLabel(e.category)}</td>
                        <td className="px-4 py-3 text-muted-foreground">{typeLabel(e.expense_type)}</td>
                        <td className="px-4 py-3 text-foreground">{formatMoney(toNumber(e.amount))}</td>
                        <td className="px-4 py-3 text-muted-foreground">{e.product_name ?? '—'}</td>
                        <td className="px-4 py-3 text-muted-foreground">{formatDate(e.created_at)}</td>
                        <td className="px-4 py-3 text-right">
                          <button
                            type="button"
                            onClick={() => { setEditing(e); setShowForm(true); setNotice(null); }}
                            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted"
                            aria-label="Edit expense"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => { setExpenseToDelete(e); setDeleteError(null); }}
                            className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-muted"
                            aria-label="Delete expense"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </motion.div>
        </>
      )}

      <AnimatePresence>
        {showForm && (
          <ExpenseFormModal
            editing={editing}
            onClose={() => { setShowForm(false); setEditing(null); }}
            onSuccess={(msg) => {
              setShowForm(false);
              setEditing(null);
              setNotice(msg);
              fetchExpenses();
            }}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {expenseToDelete != null && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/60 backdrop-blur-sm z-50"
              onClick={() => { setExpenseToDelete(null); setDeleteError(null); }}
            />
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full max-w-sm bg-card border border-border rounded-xl shadow-xl p-6 pointer-events-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 className="font-semibold text-foreground mb-1">Delete expense</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Delete <strong>{expenseToDelete.description}</strong>? This cannot be undone.
                </p>
                {deleteError && (
                  <p className="text-sm text-destructive mb-3">{deleteError}</p>
                )}
                <div className="flex gap-3 justify-end">
                  <button
                    type="button"
                    onClick={() => { setExpenseToDelete(null); setDeleteError(null); }}
                    className="px-4 py-2 rounded-lg border border-border bg-card text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={async () => {
                      setDeleting(true);
                      setDeleteError(null);
                      try {
                        await expensesAPI.delete(expenseToDelete.id);
                        setExpenseToDelete(null);
                        setNotice('Expense deleted');
                        fetchExpenses();
                      } catch (err: unknown) {
                        setDeleteError(expenseApiError(err, 'Failed to delete expense'));
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
    </motion.div>
  );
}

function ExpenseFormModal({
  editing,
  onClose,
  onSuccess,
}: {
  editing: ExpenseResponse | null;
  onClose: () => void;
  onSuccess: (msg: string) => void;
}) {
  const [fields, setFields] = useState<ExpenseFormFields>(editing ? formFromExpense(editing) : emptyForm());
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    if (editing) {
      const parsed = buildExpenseUpdatePayload(fields);
      if (!parsed.ok) { setErr(parsed.error); return; }
      setSubmitting(true);
      expensesAPI
        .update(editing.id, parsed.body)
        .then(() => onSuccess('Expense updated'))
        .catch((error) => setErr(expenseApiError(error, 'Failed to update expense')))
        .finally(() => setSubmitting(false));
      return;
    }
    const parsed = buildExpenseCreatePayload(fields);
    if (!parsed.ok) { setErr(parsed.error); return; }
    setSubmitting(true);
    expensesAPI
      .create(parsed.body)
      .then(() => onSuccess('Expense created'))
      .catch((error) => setErr(expenseApiError(error, 'Failed to create expense')))
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
            <h3 className="font-semibold text-foreground">{editing ? 'Edit expense' : 'Add expense'}</h3>
            <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-5 h-5" /></button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Category *</label>
              <select
                value={fields.category}
                onChange={(e) => setFields((f) => ({ ...f, category: e.target.value }))}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm"
              >
                {EXPENSE_CATEGORY_ORDER.map((key) => (
                  <option key={key} value={key}>{categoryLabel(key)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Description *</label>
              <input
                value={fields.description}
                onChange={(e) => setFields((f) => ({ ...f, description: e.target.value }))}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={fields.amount}
                  onChange={(e) => setFields((f) => ({ ...f, amount: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Type *</label>
                <select
                  value={fields.expenseType}
                  onChange={(e) => setFields((f) => ({ ...f, expenseType: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm"
                >
                  {EXPENSE_TYPE_ORDER.map((key) => (
                    <option key={key} value={key}>{typeLabel(key)}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Product ID (optional)</label>
              <input
                value={fields.productId}
                onChange={(e) => setFields((f) => ({ ...f, productId: e.target.value }))}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm"
              />
            </div>
            {err && <p className="text-sm text-destructive">{err}</p>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-border text-foreground text-sm font-medium hover:bg-accent">Cancel</button>
              <button type="submit" disabled={submitting} className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 disabled:opacity-50">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin inline" /> : (editing ? 'Save' : 'Create')}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </>
  );
}
