import { motion } from 'framer-motion';
import { StatCard } from '@/components/shared/StatCard';
import { kpiData } from '@/data/mockDashboard';

export function KPICards() {
  return (
    <motion.div
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4"
      initial="hidden"
      animate="show"
      variants={{ show: { transition: { staggerChildren: 0.06 } } }}
    >
      {kpiData.map((kpi, i) => (
        <StatCard key={kpi.label} data={kpi} index={i} />
      ))}
    </motion.div>
  );
}
