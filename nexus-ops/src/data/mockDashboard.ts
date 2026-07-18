import { KPIData, ChartDataPoint, AIAlert } from './types';

export const kpiData: KPIData[] = [
  {
    label: 'Inventory Health',
    value: 87,
    suffix: '%',
    trend: 3.2,
    trendLabel: 'vs last month',
    updatedAgo: '2h ago',
    icon: 'Activity',
    accentColor: 'cyan',
  },
  {
    label: 'Expenses vs Budget',
    value: 142500,
    prefix: '$',
    trend: -2.1,
    trendLabel: 'under budget',
    updatedAgo: '1h ago',
    icon: 'DollarSign',
    accentColor: 'primary',
  },
  {
    label: 'Vendor Reliability',
    value: 94.2,
    suffix: '%',
    trend: 1.8,
    trendLabel: 'improvement',
    updatedAgo: '3h ago',
    icon: 'Shield',
    accentColor: 'emerald',
  },
  {
    label: 'Stockout Risk',
    value: 12,
    suffix: ' items',
    trend: 4,
    trendLabel: 'at risk',
    updatedAgo: '30m ago',
    icon: 'AlertTriangle',
    accentColor: 'orange',
  },
  {
    label: 'Active AI Alerts',
    value: 7,
    trend: 2,
    trendLabel: 'new today',
    updatedAgo: 'Just now',
    icon: 'Brain',
    accentColor: 'magenta',
  },
];

export const salesTrendData: ChartDataPoint[] = [
  { name: 'Jan', value: 42000 },
  { name: 'Feb', value: 38000 },
  { name: 'Mar', value: 51000 },
  { name: 'Apr', value: 47000 },
  { name: 'May', value: 53000 },
  { name: 'Jun', value: 59000 },
  { name: 'Jul', value: 62000 },
  { name: 'Aug', value: 55000 },
  { name: 'Sep', value: 68000 },
  { name: 'Oct', value: 72000 },
  { name: 'Nov', value: 64000 },
  { name: 'Dec', value: 78000 },
];

export const inventoryMovementData: ChartDataPoint[] = [
  { name: 'Jan', value: 1200, value2: 980 },
  { name: 'Feb', value: 1100, value2: 1050 },
  { name: 'Mar', value: 1350, value2: 1200 },
  { name: 'Apr', value: 1280, value2: 1150 },
  { name: 'May', value: 1420, value2: 1300 },
  { name: 'Jun', value: 1500, value2: 1380 },
];

export const expenseBreakdownData: ChartDataPoint[] = [
  { name: 'Raw Materials', value: 45000 },
  { name: 'Logistics', value: 28000 },
  { name: 'Operations', value: 18000 },
  { name: 'Marketing', value: 12000 },
  { name: 'Technology', value: 9500 },
];

export const vendorPerformanceData: ChartDataPoint[] = [
  { name: 'Jan', value: 88, value2: 82 },
  { name: 'Feb', value: 91, value2: 85 },
  { name: 'Mar', value: 87, value2: 88 },
  { name: 'Apr', value: 93, value2: 86 },
  { name: 'May', value: 95, value2: 89 },
  { name: 'Jun', value: 92, value2: 91 },
];

export const aiAlerts: AIAlert[] = [
  {
    id: '1',
    title: 'Potential stockout: SKU-4821 (Steel Bearings)',
    riskLevel: 'critical',
    confidence: 94,
    explanation: 'Current consumption rate of 340 units/week with only 520 units remaining. Lead time from primary vendor is 14 days. Reorder point will be breached in 4 days.',
    recommendation: 'Place emergency order with Vendor B (FastParts Inc) who offers 7-day express delivery.',
    timestamp: '10 min ago',
  },
  {
    id: '2',
    title: 'Vendor price anomaly detected: GlobalTech Solutions',
    riskLevel: 'high',
    confidence: 87,
    explanation: 'Latest invoice shows 18% price increase on component XR-200 compared to contracted rate. This deviates significantly from the 3% annual adjustment clause.',
    recommendation: 'Flag for procurement review. Consider triggering contract renegotiation clause.',
    timestamp: '1h ago',
  },
  {
    id: '3',
    title: 'Delivery delay pattern: Pacific Logistics',
    riskLevel: 'medium',
    confidence: 78,
    explanation: 'Last 5 shipments averaged 3.2 days late. On-time delivery rate dropped from 96% to 81% over past quarter.',
    recommendation: 'Schedule vendor performance review. Prepare backup logistics partner comparison.',
    timestamp: '2h ago',
  },
  {
    id: '4',
    title: 'Seasonal demand spike predicted for Q2',
    riskLevel: 'low',
    confidence: 91,
    explanation: 'Historical data shows 28% demand increase for electronics components in Q2. Current inventory levels may be insufficient.',
    recommendation: 'Increase safety stock levels by 15% for top 20 SKUs before March 15.',
    timestamp: '4h ago',
  },
];
