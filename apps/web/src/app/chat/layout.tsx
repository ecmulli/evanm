import type { Metadata } from 'next';
import './chat.css';

export const metadata: Metadata = {
  title: 'Chat',
  robots: { index: false, follow: false },
};

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
