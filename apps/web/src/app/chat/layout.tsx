import type { Metadata, Viewport } from 'next';
import './chat.css';
import { PwaRegister } from '@/components/chat/PwaRegister';

export const metadata: Metadata = {
  title: 'Claude Chat',
  manifest: '/chat.webmanifest',
  robots: { index: false, follow: false },
  appleWebApp: { capable: true, statusBarStyle: 'black-translucent', title: 'Claude' },
};

export const viewport: Viewport = {
  themeColor: '#262624',
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
};

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return <>{children}<PwaRegister /></>;
}
