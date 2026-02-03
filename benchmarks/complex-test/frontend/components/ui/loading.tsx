'use client';

import { IconLoader } from './icons';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <IconLoader className={`${sizeClasses[size]} animate-spin text-primary-500 ${className}`} />
  );
}

interface LoadingPageProps {
  message?: string;
}

export function LoadingPage({ message = '読み込み中...' }: LoadingPageProps) {
  return (
    <div className="page-container flex items-center justify-center">
      <div className="text-center animate-fade-in">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-sand-200 animate-pulse" />
          <div className="absolute inset-0 flex items-center justify-center">
            <LoadingSpinner size="lg" />
          </div>
        </div>
        <p className="mt-4 text-sand-600 font-medium">{message}</p>
      </div>
    </div>
  );
}

export function LoadingCard() {
  return (
    <div className="card p-6 animate-pulse">
      <div className="skeleton h-4 w-24 mb-4" />
      <div className="skeleton h-8 w-16 mb-2" />
      <div className="skeleton h-3 w-32" />
    </div>
  );
}

export function LoadingList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card p-4 animate-pulse">
          <div className="flex items-center gap-4">
            <div className="skeleton w-12 h-12 rounded-full" />
            <div className="flex-1">
              <div className="skeleton h-4 w-32 mb-2" />
              <div className="skeleton h-3 w-48" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
