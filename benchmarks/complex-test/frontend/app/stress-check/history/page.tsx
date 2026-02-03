'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { stressCheckApi, StressCheckHistoryItem } from '@/lib/api/stress-check';
import { Header } from '@/components/ui/header';
import { IconHistory, IconChevronRight, IconCalendar, IconSmile, IconFrown, IconLoader } from '@/components/ui/icons';

export default function StressCheckHistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<StressCheckHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const data = await stressCheckApi.getHistory();
        setHistory(data);
      } catch (err: any) {
        setError('履歴の取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, []);

  const formatPeriod = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getFullYear()}年${date.getMonth() + 1}月`;
  };

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <IconLoader className="w-10 h-10 animate-spin text-primary-500 mx-auto mb-4" />
          <p className="text-sand-600">履歴を読み込んでいます...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <Header title="受検履歴" showHome />

      <main className="page-content">
        {/* Header Card */}
        <div className="card p-6 mb-6 animate-fade-in">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-100 to-accent-200 flex items-center justify-center">
              <IconHistory className="w-6 h-6 text-accent-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-sand-900">ストレスチェック履歴</h1>
              <p className="text-sm text-sand-600">過去の受検結果を確認できます</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="alert-danger mb-6 animate-fade-in-down">{error}</div>
        )}

        {history.length === 0 ? (
          <div className="card p-12 text-center animate-fade-in">
            <div className="w-16 h-16 rounded-full bg-sand-100 flex items-center justify-center mx-auto mb-4">
              <IconHistory className="w-8 h-8 text-sand-400" />
            </div>
            <h2 className="text-lg font-bold text-sand-800 mb-2">履歴がありません</h2>
            <p className="text-sand-600 mb-6">まだストレスチェックを受検していません</p>
            <button
              onClick={() => router.push('/stress-check')}
              className="btn-primary"
            >
              ストレスチェックを受ける
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {history.map((item, idx) => (
              <div
                key={item.id}
                onClick={() => router.push(`/stress-check/result/${item.id}`)}
                className="card-interactive p-5 group animate-fade-in-up"
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      item.is_high_stress
                        ? 'bg-gradient-to-br from-danger-light to-red-100'
                        : 'bg-gradient-to-br from-success-light to-green-100'
                    }`}>
                      {item.is_high_stress ? (
                        <IconFrown className="w-6 h-6 text-danger" />
                      ) : (
                        <IconSmile className="w-6 h-6 text-success" />
                      )}
                    </div>

                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <IconCalendar className="w-4 h-4 text-sand-400" />
                        <span className="font-bold text-sand-900">{formatPeriod(item.period)}</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <span className="text-sand-600">総合スコア: <span className="font-semibold text-sand-800">{item.total_score}</span></span>
                        <span className={`badge ${item.is_high_stress ? 'badge-danger' : 'badge-success'}`}>
                          {item.is_high_stress ? '高ストレス' : '正常範囲'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <IconChevronRight className="w-5 h-5 text-sand-400 group-hover:text-primary-500 group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex gap-4">
          <button
            onClick={() => router.push('/stress-check')}
            className="btn-primary"
          >
            新しくチェックを受ける
          </button>
          <button
            onClick={() => router.push('/home')}
            className="btn-secondary"
          >
            ホームに戻る
          </button>
        </div>
      </main>
    </div>
  );
}
