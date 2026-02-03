'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api/auth';
import { IconBrain, IconMail, IconLock, IconBuilding, IconLoader, IconCheckCircle } from '@/components/ui/icons';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    company_name: '',
    industry: '',
    plan_type: 'basic',
    email: '',
    password: '',
    password_confirm: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handlePasswordChange = (field: 'password' | 'password_confirm', value: string) => {
    const newFormData = { ...formData, [field]: value };
    setFormData(newFormData);

    if (field === 'password' && value.length > 0 && value.length < 8) {
      setError('パスワードは8文字以上で入力してください');
    } else if (field === 'password_confirm' && newFormData.password !== value && value.length > 0) {
      setError('パスワードが一致しません');
    } else if (newFormData.password === newFormData.password_confirm && newFormData.password.length >= 8) {
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateEmail(formData.email)) {
      setError('有効なメールアドレスを入力してください');
      return;
    }

    if (formData.password !== formData.password_confirm) {
      setError('パスワードが一致しません');
      return;
    }

    if (formData.password.length < 8) {
      setError('パスワードは8文字以上で入力してください');
      return;
    }

    setLoading(true);

    try {
      const response = await authApi.register(formData);
      setError('');
      setSuccess(true);

      setTimeout(() => {
        if (response.user.role === 'admin') {
          router.push('/dashboard');
        } else {
          router.push('/home');
        }
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || '登録に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const industries = [
    { value: '', label: '業種を選択してください' },
    { value: 'IT', label: 'IT・通信' },
    { value: '広告', label: '広告・メディア' },
    { value: '介護', label: '介護・医療' },
    { value: '運送', label: '運送・物流' },
    { value: '建設', label: '建設・不動産' },
    { value: '製造', label: '製造業' },
    { value: '小売', label: '小売・サービス' },
    { value: 'その他', label: 'その他' },
  ];

  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-sand-50 to-white overflow-y-auto">
        <div className="w-full max-w-lg animate-fade-in py-8">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-glow">
              <IconBrain className="w-7 h-7 text-white" />
            </div>
            <span className="text-xl font-bold text-sand-900">StressAgent Pro</span>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-sand-900 mb-2">新規登録</h2>
            <p className="text-sand-600">企業アカウントを作成してください</p>
          </div>

          {success ? (
            <div className="card p-8 text-center animate-scale-in">
              <div className="w-16 h-16 rounded-full bg-success-light flex items-center justify-center mx-auto mb-4">
                <IconCheckCircle className="w-8 h-8 text-success" />
              </div>
              <h3 className="text-xl font-bold text-sand-900 mb-2">登録完了</h3>
              <p className="text-sand-600 mb-4">アカウントが作成されました</p>
              <p className="text-sm text-sand-500">ダッシュボードに移動しています...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Company Info Section */}
              <div className="card p-6">
                <h3 className="font-semibold text-sand-800 mb-4 flex items-center gap-2">
                  <IconBuilding className="w-5 h-5 text-primary-500" />
                  企業情報
                </h3>

                <div className="space-y-4">
                  <div>
                    <label htmlFor="companyName" className="label">企業名</label>
                    <input
                      id="companyName"
                      type="text"
                      required
                      value={formData.company_name}
                      onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                      className="input"
                      placeholder="株式会社サンプル"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="industry" className="label">業種</label>
                      <select
                        id="industry"
                        value={formData.industry}
                        onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                        className="select"
                      >
                        {industries.map((ind) => (
                          <option key={ind.value} value={ind.value}>{ind.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label htmlFor="planType" className="label">プラン</label>
                      <select
                        id="planType"
                        value={formData.plan_type}
                        onChange={(e) => setFormData({ ...formData, plan_type: e.target.value })}
                        className="select"
                      >
                        <option value="basic">ベーシック</option>
                        <option value="premium">プレミアム</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              {/* Account Info Section */}
              <div className="card p-6">
                <h3 className="font-semibold text-sand-800 mb-4 flex items-center gap-2">
                  <IconMail className="w-5 h-5 text-primary-500" />
                  アカウント情報
                </h3>

                <div className="space-y-4">
                  <div>
                    <label htmlFor="email" className="label">メールアドレス</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <IconMail className="w-5 h-5 text-sand-400" />
                      </div>
                      <input
                        id="email"
                        type="email"
                        required
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="input pl-12"
                        placeholder="admin@company.com"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="password" className="label">パスワード</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <IconLock className="w-5 h-5 text-sand-400" />
                      </div>
                      <input
                        id="password"
                        type="password"
                        required
                        value={formData.password}
                        onChange={(e) => handlePasswordChange('password', e.target.value)}
                        className="input pl-12"
                        placeholder="8文字以上"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="passwordConfirm" className="label">パスワード確認</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <IconLock className="w-5 h-5 text-sand-400" />
                      </div>
                      <input
                        id="passwordConfirm"
                        type="password"
                        required
                        value={formData.password_confirm}
                        onChange={(e) => handlePasswordChange('password_confirm', e.target.value)}
                        className="input pl-12"
                        placeholder="パスワードを再入力"
                      />
                    </div>
                  </div>
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
                    <span>登録中...</span>
                  </>
                ) : (
                  '登録する'
                )}
              </button>
            </form>
          )}

          <div className="mt-8 text-center">
            <p className="text-sand-600">
              すでにアカウントをお持ちですか？{' '}
              <a href="/login" className="text-primary-600 hover:text-primary-700 font-medium transition-colors">
                ログイン
              </a>
            </p>
          </div>
        </div>
      </div>

      {/* Right side - Decorative */}
      <div className="hidden lg:flex lg:w-2/5 bg-gradient-to-br from-primary-600 via-primary-500 to-primary-700 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="decorative-blob w-96 h-96 bg-primary-400 top-20 -right-20" />
          <div className="decorative-blob w-80 h-80 bg-accent-400 bottom-20 left-20 opacity-20" />
        </div>

        <div className="relative z-10 flex flex-col justify-center px-12 text-white">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <IconBrain className="w-8 h-8" />
            </div>
            <span className="text-2xl font-bold">StressAgent Pro</span>
          </div>

          <h2 className="text-3xl font-bold mb-6">
            メンタルヘルスケアを<br />
            次のレベルへ
          </h2>

          <div className="space-y-4">
            {[
              '厚労省指針に準拠したストレスチェック',
              'AIによるリアルタイム分析',
              '従業員へのパーソナルサポート',
              '管理者向けダッシュボード',
            ].map((feature, i) => (
              <div key={i} className="flex items-center gap-3 animate-fade-in-up" style={{ animationDelay: `${i * 100}ms` }}>
                <div className="w-6 h-6 rounded-full bg-accent-400/20 flex items-center justify-center">
                  <IconCheckCircle className="w-4 h-4 text-accent-300" />
                </div>
                <span className="text-primary-100">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
