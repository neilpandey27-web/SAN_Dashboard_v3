import type { Metadata } from 'next';
import 'bootstrap/dist/css/bootstrap.min.css';
import '@/styles/globals.css';
import { AuthProvider } from '@/lib/auth';
import { TenantProvider } from '@/contexts/TenantContext';

export const metadata: Metadata = {
  title: 'OneIT SAN Analytics Dashboard',
  description: 'Monitor and manage IBM storage capacity',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-bs-theme="dark">
      <body>
        <AuthProvider>
          <TenantProvider>
            {children}
          </TenantProvider>
        </AuthProvider>
      </body>
    </html>
  );
}