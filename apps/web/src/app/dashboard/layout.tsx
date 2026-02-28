import type { Metadata, Viewport } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard | evanm.xyz',
  description: 'Unified task and to-do dashboard',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Task Dashboard',
  },
  icons: {
    apple: '/icons/icon-192.png',
  },
};

export const viewport: Viewport = {
  themeColor: '#152A54',
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
