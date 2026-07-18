import axios from 'axios';

const rawApiUrl = import.meta.env.VITE_API_URL as string | undefined;
if (import.meta.env.PROD && (!rawApiUrl || !rawApiUrl.startsWith('http'))) {
  throw new Error('VITE_API_URL must be set to the backend API URL in production (e.g. https://api.example.com).');
}
export const API_URL = import.meta.env.DEV ? (rawApiUrl ?? 'http://localhost:8000') : rawApiUrl!;
const baseURL = import.meta.env.DEV ? '' : rawApiUrl!;

const api = axios.create({
  baseURL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

const getToken = () => localStorage.getItem('access_token');
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/';
    }
    return Promise.reject(err);
  }
);

export const authAPI = {
  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    return api.post<{ access_token: string; token_type: string }>('/api/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  register: (email: string, password: string) =>
    api.post('/api/auth/register', { email, password, role: 'admin' }),
  getMe: () => api.get<{ id: number; email: string; role: string }>('/api/auth/me'),
};

export const dashboardAPI = {
  revenue: (days = 30) => api.get('/api/dashboard/revenue', { params: { days } }),
  expenses: (days = 30) => api.get('/api/dashboard/expenses', { params: { days } }),
  profit: (days = 30) => api.get('/api/dashboard/profit', { params: { days } }),
  stockStatus: () => api.get('/api/dashboard/stock-status'),
  sales: (days = 30) => api.get('/api/dashboard/sales', { params: { days } }),
};

export const aiAPI = {
  alerts: (params?: { skip?: number; limit?: number }) => api.get('/api/ai/alerts', { params }),
};

export interface VendorRanking {
  vendor_id: number;
  vendor_name: string;
  overall_score: number | null;
  reliability_score: number | null;
  cost_score: number | null;
  avg_lead_time_days: number | null;
  is_active: boolean;
  explanation: string;
}

export interface VendorProduct {
  vendor_product_id: number;
  product_id: number;
  product_name: string;
  unit_cost: number;
  min_order_qty: number;
  lead_time_days: number | null;
}

export interface PurchaseOrderItemCreate {
  product_id: number;
  quantity: number;
  unit_cost: number;
}

export interface PurchaseOrderCreate {
  vendor_id: number;
  items: PurchaseOrderItemCreate[];
  promised_delivery_date?: string | null;
}

export interface PurchaseOrderItemResponse {
  product_id: number;
  product_name: string;
  quantity: number;
  unit_cost: number;
  total_cost: number;
}

export interface PurchaseOrderResponse {
  id: number;
  vendor_id: number;
  vendor_name: string;
  po_number: string;
  status: string;
  total_cost: number;
  order_date: string;
  promised_delivery_date: string | null;
  actual_delivery_date: string | null;
  items: PurchaseOrderItemResponse[];
}

export const vendorsAPI = {
  rankings: (params?: { product_id?: number }) =>
    api.get<VendorRanking[]>('/api/vendors/rankings', { params }),
  vendorProducts: (vendorId: number) =>
    api.get<VendorProduct[]>(`/api/vendors/${vendorId}/products`),
  delete: (vendorId: number) =>
    api.delete(`/api/vendors/${vendorId}`),
};

export const purchaseOrdersAPI = {
  create: (body: PurchaseOrderCreate) =>
    api.post<PurchaseOrderResponse>('/api/purchase-orders', body),
  list: (params?: { vendor_id?: number }) =>
    api.get<PurchaseOrderResponse[]>('/api/purchase-orders', { params }),
};

// Products (SKUs)
export interface ProductCreate {
  name: string;
  description?: string;
  price: number;
  stock_quantity?: number;
  stock_threshold?: number;
}

export interface ProductResponse {
  id: number;
  name: string;
  description: string | null;
  price: number;
  stock_quantity: number;
  stock_threshold: number;
  created_at: string;
  updated_at: string | null;
}

export const productsAPI = {
  list: (params?: { search?: string; limit?: number }) =>
    api.get<ProductResponse[]>('/api/products', { params: { limit: 100, ...params } }),
  create: (body: ProductCreate) =>
    api.post<ProductResponse>('/api/products', body),
};

// Inventory (stock in/out)
export const inventoryAPI = {
  stockIn: (product_id: number, quantity: number, reason?: string) =>
    api.post('/api/inventory/stock-in', { product_id, quantity, reason: reason ?? 'Manual restock' }),
  stockOut: (product_id: number, quantity: number, reason?: string) =>
    api.post('/api/inventory/stock-out', { product_id, quantity, reason: reason ?? 'Sale' }),
};

// Vendor create + add product to vendor
export interface VendorCreate {
  name: string;
  is_active?: boolean;
  avg_lead_time_days?: number;
  reliability_score?: number;
  cost_score?: number;
  overall_score?: number;
}

export interface VendorCreateResponse {
  id: number;
  name: string;
  is_active: boolean;
  avg_lead_time_days: number | null;
  reliability_score: number | null;
  cost_score: number | null;
  overall_score: number | null;
}

export interface VendorProductCreate {
  product_id: number;
  unit_cost: number;
  min_order_qty?: number;
  lead_time_days?: number;
}

export const vendorsCreateAPI = {
  create: (body: VendorCreate) =>
    api.post<VendorCreateResponse>('/api/vendors', body),
  addProduct: (vendorId: number, body: VendorProductCreate) =>
    api.post<VendorProductResponse>(`/api/vendors/${vendorId}/products`, body),
};

export default api;
