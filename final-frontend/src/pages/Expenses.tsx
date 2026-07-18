import { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { expensesBudgetData } from '@/data/mockData';

export default function Expenses() {
  const [selectedDept, setSelectedDept] = useState<string | null>(null);
  const data = selectedDept ? expensesBudgetData.filter(d => d.dept === selectedDept) : expensesBudgetData;

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
  const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-6">
      {/* Department filter */}
      <motion.div variants={fadeUp} className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedDept(null)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${!selectedDept ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
        >
          All Departments
        </button>
        {expensesBudgetData.map(d => (
          <button
            key={d.dept}
            onClick={() => setSelectedDept(d.dept === selectedDept ? null : d.dept)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${selectedDept === d.dept ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
          >
            {d.dept}
          </button>
        ))}
      </motion.div>

      {/* Chart */}
      <motion.div variants={fadeUp} className="bg-card border border-border rounded-xl p-5 card-shadow">
        <h3 className="font-semibold text-foreground text-sm mb-4">Budget vs Actual</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="dept" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
            <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
            <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: 12 }} />
            <Bar dataKey="budget" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} name="Budget" />
            <Bar dataKey="actual" radius={[4, 4, 0, 0]} name="Actual">
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.actual > entry.budget ? 'hsl(var(--critical))' : 'hsl(var(--success))'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Department Cards */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {expensesBudgetData.map(d => {
          const overBudget = d.actual > d.budget;
          const pct = ((d.actual / d.budget) * 100).toFixed(1);
          return (
            <div key={d.dept} className="bg-card border border-border rounded-xl p-4 card-shadow hover:card-shadow-hover transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-foreground">{d.dept}</h4>
                <span className={`text-xs font-medium ${overBudget ? 'text-critical' : 'text-success'}`}>
                  {pct}%
                </span>
              </div>
              <div className="space-y-1 text-xs text-muted-foreground">
                <div className="flex justify-between"><span>Budget</span><span className="text-foreground">${(d.budget / 1000).toFixed(0)}k</span></div>
                <div className="flex justify-between"><span>Actual</span><span className="text-foreground">${(d.actual / 1000).toFixed(0)}k</span></div>
                <div className="flex justify-between"><span>Variance</span><span className={overBudget ? 'text-critical' : 'text-success'}>${(Math.abs(d.actual - d.budget) / 1000).toFixed(0)}k {overBudget ? 'over' : 'under'}</span></div>
              </div>
              <div className="mt-3 h-1.5 bg-secondary rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, +pct)}%` }}
                  transition={{ duration: 0.8 }}
                  className={`h-full rounded-full ${overBudget ? 'bg-critical' : 'bg-success'}`}
                />
              </div>
            </div>
          );
        })}
      </motion.div>
    </motion.div>
  );
}
