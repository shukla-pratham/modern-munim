import { ChartWrapper } from '@/components/shared/ChartWrapper';
import {
  salesTrendData,
  inventoryMovementData,
  expenseBreakdownData,
  vendorPerformanceData,
} from '@/data/mockDashboard';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const chartColors = {
  primary: 'hsl(217, 91%, 53%)',
  cyan: 'hsl(188, 95%, 43%)',
  orange: 'hsl(25, 95%, 53%)',
  magenta: 'hsl(330, 81%, 60%)',
  emerald: 'hsl(160, 84%, 39%)',
  muted: 'hsl(222, 30%, 25%)',
};

const pieColors = [chartColors.primary, chartColors.cyan, chartColors.emerald, chartColors.orange, chartColors.magenta];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-strong rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="font-semibold">
          {entry.name}: {typeof entry.value === 'number' && entry.value > 1000 ? `$${(entry.value / 1000).toFixed(0)}k` : entry.value}
        </p>
      ))}
    </div>
  );
};

export function DashboardCharts() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ChartWrapper title="Sales Trend" subtitle="Monthly revenue over the past year">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={salesTrendData}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.muted} opacity={0.3} />
            <XAxis dataKey="name" stroke={chartColors.muted} fontSize={11} />
            <YAxis stroke={chartColors.muted} fontSize={11} tickFormatter={(v) => `$${v / 1000}k`} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="value"
              stroke={chartColors.cyan}
              strokeWidth={2.5}
              dot={{ fill: chartColors.cyan, r: 3 }}
              activeDot={{ r: 5, fill: chartColors.cyan }}
              name="Revenue"
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartWrapper>

      <ChartWrapper title="Inventory Movement" subtitle="Units received vs dispatched">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={inventoryMovementData}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.muted} opacity={0.3} />
            <XAxis dataKey="name" stroke={chartColors.muted} fontSize={11} />
            <YAxis stroke={chartColors.muted} fontSize={11} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="value" fill={chartColors.primary} name="Received" radius={[4, 4, 0, 0]} />
            <Bar dataKey="value2" fill={chartColors.cyan} name="Dispatched" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartWrapper>

      <ChartWrapper title="Expense Breakdown" subtitle="Distribution by category this month">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={expenseBreakdownData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={3}
              dataKey="value"
              nameKey="name"
              strokeWidth={0}
            >
              {expenseBreakdownData.map((_, i) => (
                <Cell key={i} fill={pieColors[i % pieColors.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend iconType="circle" iconSize={8} formatter={(v) => <span className="text-xs text-muted-foreground">{v}</span>} />
          </PieChart>
        </ResponsiveContainer>
      </ChartWrapper>

      <ChartWrapper title="Vendor Performance" subtitle="Top vs average vendor scores trend">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={vendorPerformanceData}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.muted} opacity={0.3} />
            <XAxis dataKey="name" stroke={chartColors.muted} fontSize={11} />
            <YAxis stroke={chartColors.muted} fontSize={11} domain={[70, 100]} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line type="monotone" dataKey="value" stroke={chartColors.emerald} strokeWidth={2.5} dot={{ r: 3 }} name="Top Vendor" />
            <Line type="monotone" dataKey="value2" stroke={chartColors.orange} strokeWidth={2.5} dot={{ r: 3 }} name="Average" strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </ChartWrapper>
    </div>
  );
}
