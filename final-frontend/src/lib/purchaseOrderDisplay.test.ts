import { describe, expect, it } from 'vitest';
import {
  EMPTY_PO_LIST_MESSAGE,
  buildPurchaseOrderCreatePayload,
  isDeliveredStatus,
  poApiError,
  poList,
  poStatus,
} from '@/lib/purchaseOrderDisplay';
import type { PurchaseOrderResponse } from '@/lib/api';

function po(partial: Partial<PurchaseOrderResponse> = {}): PurchaseOrderResponse {
  return {
    id: 1,
    vendor_id: 2,
    vendor_name: 'Acme',
    po_number: 'PO-TEST-1',
    status: 'created',
    total_cost: 12,
    order_date: '2026-08-14T00:00:00Z',
    promised_delivery_date: null,
    actual_delivery_date: null,
    items: [
      {
        product_id: 10,
        product_name: 'Widget',
        quantity: 3,
        unit_cost: 4,
        total_cost: 12,
      },
    ],
    ...partial,
  };
}

describe('purchaseOrderDisplay', () => {
  it('maps create payload to lowercase snake_case API fields', () => {
    const result = buildPurchaseOrderCreatePayload({
      vendorId: 7,
      items: [{ productId: 10, quantity: 3, unitCost: 4.5 }],
    });
    expect(result).toEqual({
      ok: true,
      body: {
        vendor_id: 7,
        items: [{ product_id: 10, quantity: 3, unit_cost: 4.5 }],
      },
    });
  });

  it('rejects empty items the same way as the backend contract', () => {
    const result = buildPurchaseOrderCreatePayload({ vendorId: 1, items: [] });
    expect(result.ok).toBe(false);
  });

  it('treats missing list data as an empty PO list', () => {
    expect(poList(undefined)).toEqual([]);
    expect(poList([])).toEqual([]);
    expect(EMPTY_PO_LIST_MESSAGE).toBe('No purchase orders yet.');
  });

  it('normalizes status for timeline display without inventing values', () => {
    expect(poStatus(po({ status: 'CREATED' }))).toBe('created');
    expect(isDeliveredStatus('delivered')).toBe(true);
    expect(isDeliveredStatus('created')).toBe(false);
  });

  it('maps 401/403 without crashing', () => {
    expect(poApiError({ response: { status: 403 } })).toBe('You need admin access to view purchase orders.');
    expect(poApiError({ response: { status: 401 } })).toBe('Could not validate credentials');
    expect(poApiError({ message: 'Network Error' })).toBe('Could not reach the purchase orders API');
  });
});
