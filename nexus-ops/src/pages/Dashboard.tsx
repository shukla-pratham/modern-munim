import { MainLayout } from '@/components/layout/MainLayout';
import { KPICards } from '@/components/dashboard/KPICards';
import { DashboardCharts } from '@/components/dashboard/DashboardCharts';
import { AIAlerts } from '@/components/dashboard/AIAlerts';

export default function Dashboard() {
  return (
    <MainLayout title="Dashboard">
      <div className="space-y-6 max-w-[1400px] mx-auto">
        <KPICards />
        <DashboardCharts />
        <AIAlerts />
      </div>
    </MainLayout>
  );
}
