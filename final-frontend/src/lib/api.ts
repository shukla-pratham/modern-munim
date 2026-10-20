import axios from 'axios';

const rawApiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? '';
export const API_URL = import.meta.env.DEV ? (rawApiUrl || 'http://localhost:8000') : (rawApiUrl || window.location.origin);
const baseURL = rawApiUrl;

const api = axios.create({
  baseURL,
  // Generous timeout to tolerate cold starts on free Render tier.
  timeout: 20000,
  headers: { 'Content-Type': 'application/json' },
});

const getToken = () => localStorage.getItem('access_token');
const getActiveWorkspaceId = () => localStorage.getItem('active_workspace_id');

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const workspaceId = getActiveWorkspaceId();
  if (workspaceId) {
    config.headers['X-Workspace-Id'] = workspaceId;
  }
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

export interface AuthUser {
  id: number;
  email: string;
  role: string;
  mfa_enabled?: boolean;
  store_name?: string | null;
  store_type?: string | null;
}

export interface LoginResponse {
  access_token?: string;
  token_type?: string;
  mfa_required?: boolean;
  mfa_token?: string;
}

export interface AuthStartResponse {
  status: 'needs_onboarding' | 'authenticated';
  email: string;
  message: string;
  access_token?: string;
}

export const authAPI = {
  start: (email: string, password: string) =>
    api.post<AuthStartResponse>('/api/auth/start', { email, password }),
  onboard: (email: string, password: string, store_name: string, store_type: string) =>
    api.post<AuthStartResponse>('/api/auth/onboard', {
      email,
      password,
      store_name,
      store_type,
    }),
  /** Forgot-password: reset with email + new password directly (no OTP). */
  resetPassword: (email: string, password: string) =>
    api.post<AuthStartResponse>('/api/auth/forgot-password', { email, password }),
  updatePassword: (password: string) =>
    api.patch<AuthUser>('/api/auth/password', { password }),
  getMe: () => api.get<AuthUser>('/api/auth/me'),
  storeTypes: () => api.get<{ store_types: string[] }>('/api/auth/store-types'),
};

export const dashboardAPI = {
  revenue: (days = 30) =>
    api.get<DashboardRevenueResponse>('/api/dashboard/revenue', { params: { days } }),
  expenses: (days = 30) =>
    api.get<DashboardExpenseBreakdownResponse>('/api/dashboard/expenses', { params: { days } }),
  profit: (days = 30) =>
    api.get<DashboardProfitResponse>('/api/dashboard/profit', { params: { days } }),
  stockStatus: () =>
    api.get<DashboardStockStatusResponse>('/api/dashboard/stock-status'),
  sales: (days = 30) =>
    api.get<DashboardSalesResponse>('/api/dashboard/sales', { params: { days } }),
};

export interface DashboardDailyRevenue {
  date: string;
  revenue: number;
}

export interface DashboardRevenueResponse {
  total_revenue: number;
  period: string;
  daily_revenue: DashboardDailyRevenue[];
}

export interface DashboardMonthlyExpense {
  month: string;
  amount: number;
}

export interface DashboardExpenseBreakdownResponse {
  total_expenses: number;
  by_category: Record<string, number>;
  by_type: Record<string, number>;
  monthly_expenses: DashboardMonthlyExpense[];
}

export interface DashboardProductProfit {
  product_id: number;
  product_name: string;
  revenue: number;
  expenses: number;
  profit: number;
  margin: number;
}

export interface DashboardProfitResponse {
  total_revenue: number;
  total_expenses: number;
  net_profit: number;
  profit_margin: number;
  profit_by_product: DashboardProductProfit[];
}

export interface DashboardStockProduct {
  product_id: number;
  name: string;
  stock_quantity: number;
  threshold: number;
}

export interface DashboardStockStatusResponse {
  total_products: number;
  low_stock_products: DashboardStockProduct[];
  out_of_stock_products: DashboardStockProduct[];
  stock_value: number;
}

export interface DashboardProductSales {
  product_id: number;
  name: string;
  quantity_sold: number;
  revenue: number;
}

export interface DashboardSalesOverTime {
  date: string;
  orders: number;
  revenue: number;
}

export interface DashboardSalesResponse {
  total_sales: number;
  total_revenue: number;
  sales_by_product: DashboardProductSales[];
  sales_over_time: DashboardSalesOverTime[];
}

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
  // SPA has no receiving UI. When VITE_USE_SPRING_PRODUCTS=true, Vite sends
  // create/list/deliver under /api/purchase-orders to Spring.
};

// Customer /api/orders is Spring-migrated (with ledger) but unused by the SPA.
// TASK 18: no Orders UI exists in current or legacy frontends in this repo.
// Do not add ordersAPI unless an Orders UI / intentional cutover is approved.

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

export type VendorProductResponse = VendorProduct;

export const vendorsCreateAPI = {
  create: (body: VendorCreate) =>
    api.post<VendorCreateResponse>('/api/vendors', body),
  addProduct: (vendorId: number, body: VendorProductCreate) =>
    api.post<VendorProductResponse>(`/api/vendors/${vendorId}/products`, body),
};

export interface ExpenseResponse {
  id: number;
  category: string;
  description: string;
  amount: number;
  expense_type: string;
  product_id: number | null;
  product_name: string | null;
  created_at: string;
}

export interface ExpenseCreate {
  category: string;
  description: string;
  amount: number;
  expense_type?: string;
  product_id?: number | null;
}

export interface ExpenseUpdate {
  category?: string;
  description?: string;
  amount?: number;
  expense_type?: string;
  product_id?: number;
}

export const expensesAPI = {
  list: (params?: { skip?: number; limit?: number; category?: string; product_id?: number }) =>
    api.get<ExpenseResponse[]>('/api/expenses', { params: { limit: 100, ...params } }),
  create: (body: ExpenseCreate) =>
    api.post<ExpenseResponse>('/api/expenses', body),
  update: (id: number, body: ExpenseUpdate) =>
    api.put<ExpenseResponse>(`/api/expenses/${id}`, body),
  delete: (id: number) =>
    api.delete(`/api/expenses/${id}`),
};

export interface WorkspaceResponse {
  id: number;
  name: string;
  slug: string;
  store_type?: string | null;
  is_demo: boolean;
  onboarding_completed: boolean;
  onboarding_step: string;
  role: string;
  created_at: string;
}

export interface WorkspaceSummaryResponse {
  active_workspace: WorkspaceResponse | null;
  workspaces: WorkspaceResponse[];
  is_founder: boolean;
}

export interface WorkspaceCreate {
  name: string;
  store_type?: string;
}

export interface WorkspaceDeleteRequest {
  password: string;
}

export const workspacesAPI = {
  getCurrent: () => api.get<WorkspaceResponse>('/api/workspaces/current'),
  getSummary: () => api.get<WorkspaceSummaryResponse>('/api/workspaces/summary'),
  create: (data: WorkspaceCreate) => api.post<WorkspaceResponse>('/api/workspaces', data),
  delete: (workspaceId: number, data: { password: string }) =>
    api.post<{ message: string; deleted_id: number }>(`/api/workspaces/${workspaceId}/delete`, data),
};

export default api;
