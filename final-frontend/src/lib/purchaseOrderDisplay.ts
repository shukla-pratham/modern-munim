import type { PurchaseOrderCreate, PurchaseOrderResponse } from '@/lib/api';

export const EMPTY_PO_LIST_MESSAGE = 'No purchase orders yet.';

export function poList(rows: PurchaseOrderResponse[] | null | undefined): PurchaseOrderResponse[] {
  return rows ?? [];
}

export function poStatus(po: PurchaseOrderResponse | null | undefined): string {
  return (po?.status || 'created').toLowerCase();
}

export function isDeliveredStatus(status: string | null | undefined): boolean {
  return (status || '').toLowerCase() === 'delivered';
}

export function buildPurchaseOrderCreatePayload(input: {
  vendorId: number;
  items: { productId: number; quantity: number; unitCost: number }[];
  promisedDeliveryDate?: string | null;
}): { ok: true; body: PurchaseOrderCreate } | { ok: false; error: string } {
  if (!Number.isInteger(input.vendorId) || input.vendorId <= 0) {
    return { ok: false, error: 'Vendor is required' };
  }
  if (!input.items.length) {
    return { ok: false, error: 'At least one item is required' };
  }
  for (const item of input.items) {
    if (!Number.isInteger(item.productId) || item.productId <= 0) {
      return { ok: false, error: 'Each item needs a valid product' };
    }
    if (!Number.isInteger(item.quantity) || item.quantity <= 0) {
      return { ok: false, error: 'Each item needs a positive quantity' };
    }
    if (!Number.isFinite(item.unitCost) || item.unitCost < 0) {
      return { ok: false, error: 'Each item needs a valid unit cost' };
    }
  }
  return {
    ok: true,
    body: {
      vendor_id: input.vendorId,
      items: input.items.map((item) => ({
        product_id: item.productId,
        quantity: item.quantity,
        unit_cost: item.unitCost,
      })),
      ...(input.promisedDeliveryDate ? { promised_delivery_date: input.promisedDeliveryDate } : {}),
    },
  };
}

export function poApiError(err: unknown, fallback = 'Failed to load purchase orders.'): string {
  const ax = err as {
    response?: { data?: { detail?: unknown }; status?: number };
    message?: string;
  };
  if (ax.response?.status === 403) return 'You need admin access to view purchase orders.';
  if (ax.response?.status === 401) return 'Could not validate credentials';
  const detail = ax.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (!ax.response) return 'Could not reach the purchase orders API';
  return ax.message || fallback;
}
