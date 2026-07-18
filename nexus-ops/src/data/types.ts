export interface KPIData {
  label: string;
  value: number;
  suffix?: string;
  prefix?: string;
  trend: number;
  trendLabel: string;
  updatedAgo: string;
  icon: string;
  accentColor: 'primary' | 'cyan' | 'orange' | 'magenta' | 'emerald' | 'destructive';
}

export interface ChartDataPoint {
  name: string;
  value: number;
  value2?: number;
}

export interface AIAlert {
  id: string;
  title: string;
  riskLevel: 'critical' | 'high' | 'medium' | 'low';
  confidence: number;
  explanation: string;
  recommendation: string;
  timestamp: string;
}

export interface VendorScore {
  month: string;
  score: number;
}

export interface Vendor {
  id: string;
  name: string;
  category: string;
  overallScore: number;
  reliabilityScore: number;
  costScore: number;
  qualityScore: number;
  deliveryScore: number;
  communicationScore: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  leadTimeDays: number;
  onTimeDeliveryRate: number;
  priceVolatility: number;
  scoreHistory: VendorScore[];
  lastOrder: string;
  totalOrders: number;
  contractValue: number;
}

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
