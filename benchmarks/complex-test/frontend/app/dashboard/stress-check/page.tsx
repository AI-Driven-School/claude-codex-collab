'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api/client';
import { userApi } from '@/lib/api/user';
import { Header } from '@/components/ui/header';
import { IconClipboard, IconMail, IconDownload, IconLoader, IconUsers, IconCheckCircle, IconCalendar } from '@/components/ui/icons';

interface NonTakenUser {
  id: string;
  email: string;
  name: string;
  last_check_date: string | null;
}

interface NonTakenUsersResponse {
  period: string;
  deadline: string | null;
  users: NonTakenUser[];
  total_count: number;
  non_taken_count: number;
}

export default function DashboardStressCheckPage() {
  const router = useRouter();
  const [data, setData] = useState<NonTakenUsersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchNonTakenUsers = async () => {
      try {
        const response = await apiClient.get('/api/v1/stress-check/non-taken');
        setData(response.data);
      } catch (err: any) {
        if (err.response?.status === 401) {
          router.push('/login');
          return;
        }
        if (err.response?.status === 403) {
          setError('この機能は管理者のみ利用できます');
        } else {
          setError(err.response?.data?.detail || 'エラーが発生しました');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchNonTakenUsers();
  }, [router]);

  const handleRemind = async () => {
    try {
      if (!data || data.users.length === 0) {
        setError('送信対象がありません');
        return;
      }

      const me = await userApi.getCurrentUser();
      const companyName = me.company_name || '貴社';
      const deadline = data.deadline || data.period;
      const checkUrl = `${window.location.origin}/stress-check`;

      const recipients = data.users.map((user) => ({
        email: user.email,
        name: user.name || user.email.split('@')[0],
      }));

      await apiClient.post('/api/v1/admin/email/reminder/bulk', {
        company_name: companyName,
        deadline,
        check_url: checkUrl,
        recipients,
      });
      setSuccess('リマインドメールを送信しました');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'リマインド送信に失敗しました');
    }
  };

  const handleDownloadReport = async () => {
    try {
      const me = await userApi.getCurrentUser();
      const url = `/api/v1/reports/company/${me.company_id}/group-analysis/pdf`;
      const response = await apiClient.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = 'group_analysis_report.pdf';
      link.click();
      window.URL.revokeObjectURL(link.href);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'レポートのダウンロードに失敗しました');
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '未受検';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const completionRate = data && data.total_count > 0
    ? Math.round(((data.total_count - data.non_taken_count) / data.total_count) * 100)
    : 0;

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <IconLoader className="w-10 h-10 animate-spin text-primary-500 mx-auto mb-4" />
          <p className="text-sand-600">データを読み込んでいます...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <Header title="ストレスチェック管理" />

      <main className="page-content">
        {/* Header Card */}
        <div className="card p-6 mb-6 animate-fade-in">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
              <IconClipboard className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-sand-900">ストレスチェック管理</h1>
              <p className="text-sm text-sand-600">未受検者の確認とリマインド送信</p>
            </div>
          </div>
        </div>

        {/* Alerts */}
        {success && (
          <div className="alert-success mb-6 animate-fade-in-down">
            <IconCheckCircle className="w-5 h-5" />
            {success}
          </div>
        )}
        {error && (
          <div className="alert-danger mb-6 animate-fade-in-down">{error}</div>
        )}

        {data && (
          <>
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="stat-card animate-fade-in-up">
                <div className="flex items-center gap-2 mb-2">
                  <IconCalendar className="w-4 h-4 text-sand-400" />
                  <span className="text-xs text-sand-500">対象期間</span>
                </div>
                <div className="text-xl font-bold text-sand-900">{formatDate(data.period)}</div>
              </div>

              <div className="stat-card animate-fade-in-up" style={{ animationDelay: '50ms' }}>
                <div className="flex items-center gap-2 mb-2">
                  <IconUsers className="w-4 h-4 text-sand-400" />
                  <span className="text-xs text-sand-500">全従業員数</span>
                </div>
                <div className="text-xl font-bold text-sand-900">{data.total_count}名</div>
              </div>

              <div className="stat-card animate-fade-in-up" style={{ animationDelay: '100ms' }}>
                <div className="flex items-center gap-2 mb-2">
                  <IconClipboard className="w-4 h-4 text-danger" />
                  <span className="text-xs text-sand-500">未受検者数</span>
                </div>
                <div className="text-xl font-bold text-danger">{data.non_taken_count}名</div>
              </div>
            </div>

            {/* Completion Rate */}
            <div className="card p-5 mb-6 animate-fade-in" style={{ animationDelay: '150ms' }}>
              <div className="flex justify-between items-center mb-3">
                <span className="font-medium text-sand-700">受検率</span>
                <span className={`text-2xl font-bold ${
                  completionRate >= 80 ? 'text-success' : completionRate >= 50 ? 'text-accent-500' : 'text-danger'
                }`}>
                  {completionRate}%
                </span>
              </div>
              <div className="progress h-3">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    completionRate >= 80 ? 'bg-success' : completionRate >= 50 ? 'bg-accent-400' : 'bg-danger'
                  }`}
                  style={{ width: `${completionRate}%` }}
                />
              </div>
              <div className="mt-2 flex justify-between text-xs text-sand-500">
                <span>受検済み: {data.total_count - data.non_taken_count}名</span>
                <span>未受検: {data.non_taken_count}名</span>
              </div>
            </div>
          </>
        )}

        {/* Non-taken Users List */}
        <div className="card p-6 mb-6 animate-fade-in" style={{ animationDelay: '200ms' }}>
          <h2 className="font-bold text-sand-900 flex items-center gap-2 mb-4">
            <IconUsers className="w-5 h-5 text-primary-500" />
            未受検者一覧
          </h2>

          {!data || data.users.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-full bg-success-light flex items-center justify-center mx-auto mb-4">
                <IconCheckCircle className="w-8 h-8 text-success" />
              </div>
              <h3 className="font-bold text-sand-800 mb-2">未受検者はいません</h3>
              <p className="text-sand-600">すべての従業員がストレスチェックを受検済みです</p>
            </div>
          ) : (
            <div className="space-y-3">
              {data.users.map((user, idx) => (
                <div
                  key={user.id}
                  className="p-4 bg-sand-50 rounded-xl flex items-center justify-between animate-fade-in-up"
                  style={{ animationDelay: `${250 + idx * 30}ms` }}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-sand-200 flex items-center justify-center">
                      <span className="text-sm font-medium text-sand-600">
                        {user.name?.charAt(0) || user.email.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium text-sand-800">{user.name || '名前未設定'}</div>
                      <div className="text-sm text-sand-500">{user.email}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-sand-500">最終受検日</div>
                    <div className="text-sm font-medium text-sand-700">
                      {user.last_check_date ? formatDate(user.last_check_date) : '受検履歴なし'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-4">
          <button
            onClick={handleRemind}
            disabled={!data || data.users.length === 0}
            className="btn-primary"
          >
            <IconMail className="w-4 h-4" />
            リマインド送信
          </button>
          <button onClick={handleDownloadReport} className="btn-secondary">
            <IconDownload className="w-4 h-4" />
            レポートダウンロード
          </button>
          <button onClick={() => router.push('/dashboard')} className="btn-ghost">
            ダッシュボードに戻る
          </button>
        </div>
      </main>
    </div>
  );
}
