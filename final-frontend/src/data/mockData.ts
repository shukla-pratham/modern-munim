// ── INVENTORY ──
const categories = ['Hydraulic Systems', 'Bearings & Bushings', 'CNC Components', 'Industrial Sensors', 'Electrical Panels', 'Safety Equipment', 'Pneumatic Systems', 'Motors & Drives'];
const skuNames: [string, string][] = [
  ['HYD-PMP-2200', 'Hydraulic Axial Piston Pump 220bar'],
  ['HYD-VLV-1800', 'Directional Control Valve 4/3'],
  ['HYD-CYL-3500', 'Double Acting Cylinder 350mm'],
  ['HYD-FLT-0900', 'High Pressure Return Filter 90μm'],
  ['HYD-HOS-1200', 'Reinforced Hydraulic Hose 12mm'],
  ['BRG-BLL-6205', 'Deep Groove Ball Bearing 6205'],
  ['BRG-RLR-NU22', 'Cylindrical Roller Bearing NU220'],
  ['BRG-THR-5120', 'Thrust Ball Bearing 51200'],
  ['BRG-SLV-2540', 'Bronze Sleeve Bearing 25x40mm'],
  ['BRG-NLD-HK25', 'Drawn Cup Needle Bearing HK2520'],
  ['CNC-SPD-8000', 'High Speed Spindle Motor 8000RPM'],
  ['CNC-THL-M20S', 'Precision Tool Holder BT40-M20'],
  ['CNC-BLS-1605', 'Ball Screw Assembly 1605'],
  ['CNC-GDE-20LR', 'Linear Guide Rail 20mm'],
  ['CNC-CLT-ER32', 'ER32 Spring Collet Set'],
  ['SNS-PRS-400B', 'Pressure Transducer 0-400bar'],
  ['SNS-TMP-K500', 'K-Type Thermocouple 500°C'],
  ['SNS-PRX-M18I', 'Inductive Proximity Sensor M18'],
  ['SNS-FLW-DN25', 'Turbine Flow Meter DN25'],
  ['SNS-LVL-ULT3', 'Ultrasonic Level Sensor 3m'],
  ['ELP-MCC-400A', 'Motor Control Center 400A'],
  ['ELP-VFD-22KW', 'Variable Frequency Drive 22kW'],
  ['ELP-PLC-1214', 'Compact PLC 14DI/10DO'],
  ['ELP-HMI-10TP', '10" Touch Panel HMI'],
  ['ELP-CBR-100A', 'Molded Case Breaker 100A'],
  ['SAF-HRN-FBK5', '5-Point Safety Harness'],
  ['SAF-GGS-CHEM', 'Chemical Resistant Goggles'],
  ['SAF-GLV-HVY3', 'Heavy Duty Cut Resistant Gloves'],
  ['SAF-BTS-S3WR', 'S3 Waterproof Safety Boots'],
  ['SAF-HLM-VNT2', 'Vented Industrial Hard Hat'],
  ['PNU-CMP-7B55', 'Screw Air Compressor 7.5bar'],
  ['PNU-CYL-D40S', 'Compact Pneumatic Cylinder D40'],
  ['PNU-VLV-5P2P', '5/2 Way Solenoid Valve'],
  ['PNU-FRL-C200', 'Air Preparation Unit FRL 1/4"'],
  ['PNU-FTG-M6PL', 'Push-In Fitting M6 Elbow'],
  ['MTR-SRV-750W', 'AC Servo Motor 750W'],
  ['MTR-STP-NM23', 'Stepper Motor NEMA 23'],
  ['MTR-GBX-R060', 'Planetary Gearbox Ratio 60:1'],
  ['MTR-DRV-2AXS', 'Dual Axis Servo Drive'],
  ['MTR-ENC-4096', 'Absolute Encoder 4096 PPR'],
  ['HYD-ACC-10L4', 'Bladder Accumulator 10L 400bar'],
  ['CNC-CLP-HPC6', 'Hydraulic Power Chuck 6"'],
  ['SNS-VBR-ACCP', 'Vibration Accelerometer Piezo'],
  ['ELP-UPS-3KVA', 'Online UPS 3kVA'],
  ['SAF-SPL-LOTO', 'Lockout Tagout Station'],
  ['PNU-DRY-REF5', 'Refrigerated Air Dryer 500L/m'],
  ['MTR-BRK-24DC', 'Electromagnetic Brake 24VDC'],
  ['HYD-PPU-1100', 'Hydraulic Power Unit 11kW'],
  ['CNC-PBR-CNC5', 'CNC Probe System Wireless'],
  ['ELP-TSF-50KV', 'Dry Type Transformer 50kVA'],
];

type StockStatus = 'In Stock' | 'Low Stock' | 'Critical';

export interface InventoryItem {
  sku: string;
  name: string;
  category: string;
  price: number;
  stock: number;
  reorderPoint: number;
  status: StockStatus;
  leadTime: number;
  supplier: string;
  monthlyUsage: number[];
}

const vendorNames = [
  'Bosch Rexroth', 'Parker Hannifin', 'SKF Group', 'Siemens AG', 'ABB Ltd',
  'Festo SE', 'Mitsubishi Electric', 'Schneider Electric', 'Omron Corp', 'Fanuc Corp',
  'Eaton Corporation', 'Honeywell Intl', 'Emerson Electric', 'Rockwell Automation',
];

export const inventoryData: InventoryItem[] = skuNames.map(([sku, name], i) => {
  const catIdx = Math.floor(i / 6.25);
  const stock = Math.floor(Math.random() * 500);
  const reorderPoint = 50 + Math.floor(Math.random() * 150);
  const status: StockStatus = stock <= reorderPoint * 0.3 ? 'Critical' : stock <= reorderPoint ? 'Low Stock' : 'In Stock';
  return {
    sku,
    name,
    category: categories[catIdx] || categories[categories.length - 1],
    price: Math.floor(100 + Math.random() * 9900),
    stock,
    reorderPoint,
    status,
    leadTime: Math.floor(3 + Math.random() * 25),
    supplier: vendorNames[Math.floor(Math.random() * vendorNames.length)],
    monthlyUsage: Array.from({ length: 6 }, () => Math.floor(10 + Math.random() * 80)),
  };
});

// ── VENDORS ──
export interface Vendor {
  id: number;
  name: string;
  score: number;
  reliability: number;
  costEfficiency: number;
  quality: number;
  delivery: number;
  communication: number;
  flexibility: number;
  riskTier: 'Low' | 'Medium' | 'High';
  monthlyScores: number[];
  onTimeDelivery: number;
  priceVolatility: number[];
  activeOrders: number;
  totalSpend: number;
}

export const vendorData: Vendor[] = vendorNames.map((name, i) => {
  const score = 60 + Math.floor(Math.random() * 35);
  return {
    id: i + 1,
    name,
    score,
    reliability: 55 + Math.floor(Math.random() * 40),
    costEfficiency: 50 + Math.floor(Math.random() * 45),
    quality: 60 + Math.floor(Math.random() * 35),
    delivery: 55 + Math.floor(Math.random() * 40),
    communication: 50 + Math.floor(Math.random() * 45),
    flexibility: 50 + Math.floor(Math.random() * 45),
    riskTier: score >= 85 ? 'Low' : score >= 70 ? 'Medium' : 'High',
    monthlyScores: Array.from({ length: 6 }, () => Math.max(50, Math.min(100, score + Math.floor(Math.random() * 20 - 10)))),
    onTimeDelivery: 70 + Math.floor(Math.random() * 28),
    priceVolatility: Array.from({ length: 6 }, () => Math.random() * 15 - 5),
    activeOrders: Math.floor(Math.random() * 20),
    totalSpend: Math.floor(50000 + Math.random() * 450000),
  };
});

// ── DASHBOARD ──
export const salesTrendData = [
  { month: 'Jul', sales: 42000, orders: 380 },
  { month: 'Aug', sales: 48500, orders: 420 },
  { month: 'Sep', sales: 45200, orders: 395 },
  { month: 'Oct', sales: 52800, orders: 465 },
  { month: 'Nov', sales: 58100, orders: 510 },
  { month: 'Dec', sales: 54300, orders: 480 },
  { month: 'Jan', sales: 61200, orders: 540 },
  { month: 'Feb', sales: 67800, orders: 590 },
  { month: 'Mar', sales: 63500, orders: 555 },
  { month: 'Apr', sales: 71200, orders: 620 },
  { month: 'May', sales: 68900, orders: 605 },
  { month: 'Jun', sales: 75400, orders: 660 },
];

export const quarterlyData = [
  { quarter: 'Q1', sales: 192500, orders: 1685 },
  { quarter: 'Q2', sales: 215500, orders: 1885 },
  { quarter: 'Q3', sales: 135700, orders: 1195 },
  { quarter: 'Q4', sales: 165200, orders: 1455 },
];

export const inventoryMovementData = [
  { month: 'Jan', inbound: 420, outbound: 380, returns: 15 },
  { month: 'Feb', inbound: 480, outbound: 450, returns: 22 },
  { month: 'Mar', inbound: 390, outbound: 410, returns: 18 },
  { month: 'Apr', inbound: 520, outbound: 490, returns: 12 },
  { month: 'May', inbound: 460, outbound: 470, returns: 20 },
  { month: 'Jun', inbound: 550, outbound: 510, returns: 16 },
];

export const expenseBreakdownData = [
  { name: 'Raw Materials', value: 340000, color: 'hsl(var(--primary))' },
  { name: 'Logistics', value: 120000, color: 'hsl(var(--data))' },
  { name: 'Labor', value: 185000, color: 'hsl(var(--success))' },
  { name: 'Maintenance', value: 78000, color: 'hsl(var(--warning))' },
  { name: 'Technology', value: 95000, color: 'hsl(var(--ai))' },
  { name: 'Other', value: 42000, color: 'hsl(var(--muted-foreground))' },
];

export const vendorPerformanceData = vendorNames.slice(0, 5).map(name => ({
  name,
  data: Array.from({ length: 6 }, (_, i) => ({
    month: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'][i],
    score: 65 + Math.floor(Math.random() * 30),
  })),
}));

// ── EXPENSES ──
export const expensesBudgetData = [
  { dept: 'Operations', budget: 180000, actual: 172000 },
  { dept: 'Procurement', budget: 250000, actual: 268000 },
  { dept: 'Logistics', budget: 120000, actual: 115000 },
  { dept: 'Engineering', budget: 95000, actual: 88000 },
  { dept: 'Quality', budget: 65000, actual: 62000 },
  { dept: 'Safety', budget: 45000, actual: 48000 },
];

// ── PO ──
export const poSteps = [
  { id: 1, label: 'Requisition Created', status: 'completed' as const, date: '2025-02-10' },
  { id: 2, label: 'Manager Approval', status: 'completed' as const, date: '2025-02-12' },
  { id: 3, label: 'PO Generated', status: 'completed' as const, date: '2025-02-13' },
  { id: 4, label: 'Vendor Confirmed', status: 'active' as const, date: '2025-02-15' },
  { id: 5, label: 'Shipped', status: 'pending' as const, date: '' },
  { id: 6, label: 'Received & QC', status: 'pending' as const, date: '' },
  { id: 7, label: 'Invoice Matched', status: 'pending' as const, date: '' },
  { id: 8, label: 'Payment Released', status: 'pending' as const, date: '' },
];
