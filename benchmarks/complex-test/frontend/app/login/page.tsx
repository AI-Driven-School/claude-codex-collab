'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api/auth';
import { IconBrain, IconMail, IconLock, IconLoader, IconShield } from '@/components/ui/icons';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateEmail(email)) {
      setError('有効なメールアドレスを入力してください');
      return;
    }

    setLoading(true);

    try {
      const response = await authApi.login({ email, password });
      if (response.user.role === 'admin') {
        router.push('/dashboard');
      } else {
        router.push('/home');
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('メールアドレスまたはパスワードが正しくありません');
      } else {
        setError(err.response?.data?.detail || 'ログインに失敗しました');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Decorative */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 via-primary-500 to-primary-700 relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="decorative-blob w-96 h-96 bg-primary-400 top-20 -left-20" />
          <div className="decorative-blob w-80 h-80 bg-accent-400 bottom-20 right-20 opacity-20" />
          <div className="decorative-blob w-64 h-64 bg-white bottom-40 left-40 opacity-10" />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-12 text-white">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <IconBrain className="w-8 h-8" />
            </div>
            <span className="text-2xl font-bold">StressAgent Pro</span>
          </div>

          <h1 className="text-4xl font-bold leading-tight mb-6">
            AIで実現する<br />
            <span className="text-accent-300">働く人のメンタルヘルス</span>
          </h1>

          <p className="text-lg text-primary-100 mb-8 max-w-md">
            ストレスチェックからAIカウンセリングまで、
            従業員のウェルビーイングをサポートする統合プラットフォーム
          </p>

          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <IconShield className="w-5 h-5 text-accent-300" />
              <span>厚労省指針準拠</span>
            </div>
            <div className="flex items-center gap-2">
              <IconShield className="w-5 h-5 text-accent-300" />
              <span>個人情報保護対応</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-sand-50 to-white">
        <div className="w-full max-w-md animate-fade-in">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-glow">
              <IconBrain className="w-7 h-7 text-white" />
            </div>
            <span className="text-xl font-bold text-sand-900">StressAgent Pro</span>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-sand-900 mb-2">おかえりなさい</h2>
            <p className="text-sand-600">アカウントにログインしてください</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="label">
                メールアドレス
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <IconMail className="w-5 h-5 text-sand-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`input pl-12 ${error ? 'input-error' : ''}`}
                  placeholder="you@company.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="label">
                パスワード
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <IconLock className="w-5 h-5 text-sand-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`input pl-12 ${error ? 'input-error' : ''}`}
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <div className="alert-danger animate-fade-in-down">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full h-12 text-base"
            >
              {loading ? (
                <>
                  <IconLoader className="w-5 h-5 animate-spin" />
                  <span>ログイン中...</span>
                </>
              ) : (
                'ログイン'
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sand-600">
              アカウントをお持ちでないですか？{' '}
              <a href="/register" className="text-primary-600 hover:text-primary-700 font-medium transition-colors">
                新規登録
              </a>
            </p>
          </div>

          {/* Trust indicators */}
          <div className="mt-12 pt-8 border-t border-sand-200">
            <p className="text-center text-xs text-sand-500 mb-4">安心のセキュリティ</p>
            <div className="flex justify-center gap-6 text-sand-400">
              <div className="flex items-center gap-1.5 text-xs">
                <IconShield className="w-4 h-4" />
                <span>SSL暗号化</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs">
                <IconShield className="w-4 h-4" />
                <span>ISO27001</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
