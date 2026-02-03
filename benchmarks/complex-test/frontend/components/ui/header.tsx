'use client';

import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api/auth';
import { IconLogout, IconBrain, IconHome, IconSettings } from './icons';

interface HeaderProps {
  title?: string;
  showHome?: boolean;
  showLogout?: boolean;
  actions?: React.ReactNode;
}

export function Header({ title, showHome = false, showLogout = true, actions }: HeaderProps) {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {}
    router.push('/login');
  };

  return (
    <header className="header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-glow">
                <IconBrain className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="font-bold text-lg text-sand-900 hidden sm:block">StressAgent Pro</span>
                {title && <span className="text-sm text-sand-500 hidden sm:block">{title}</span>}
              </div>
            </div>
            {title && (
              <h1 className="text-xl font-bold text-sand-900 sm:hidden">{title}</h1>
            )}
          </div>

          <div className="flex items-center gap-2">
            {actions}
            {showHome && (
              <button
                onClick={() => router.push('/home')}
                className="icon-btn"
                aria-label="ホーム"
              >
                <IconHome className="w-5 h-5" />
              </button>
            )}
            {showLogout && (
              <button
                onClick={handleLogout}
                className="btn-secondary text-sm"
              >
                <IconLogout className="w-4 h-4" />
                <span className="hidden sm:inline">ログアウト</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
