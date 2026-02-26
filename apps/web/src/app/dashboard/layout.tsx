import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard | evanm.xyz',
  description: 'Unified task dashboard',
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
