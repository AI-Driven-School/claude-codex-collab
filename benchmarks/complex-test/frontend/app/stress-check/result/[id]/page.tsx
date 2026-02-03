'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { stressCheckApi, StressCheckResult } from '@/lib/api/stress-check';
import { Header } from '@/components/ui/header';
import { IconActivity, IconSmile, IconFrown, IconAlertTriangle, IconLoader, IconChat, IconHeart } from '@/components/ui/icons';

export default function StressCheckResultPage() {
  const params = useParams();
  const router = useRouter();
  const [result, setResult] = useState<StressCheckResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadResult = async () => {
      try {
        const data = await stressCheckApi.getResult(params.id as string);
        setResult(data);
      } catch (err: any) {
        setError('結果の取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      loadResult();
    }
  }, [params.id]);

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <IconLoader className="w-10 h-10 animate-spin text-primary-500 mx-auto mb-4" />
          <p className="text-sand-600">結果を読み込んでいます...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="card p-8 text-center max-w-md">
          <div className="w-16 h-16 rounded-full bg-danger-light flex items-center justify-center mx-auto mb-4">
            <IconAlertTriangle className="w-8 h-8 text-danger" />
          </div>
          <h2 className="text-lg font-bold text-sand-900 mb-2">エラー</h2>
          <p className="text-sand-600 mb-6">{error || '結果が見つかりません'}</p>
          <button onClick={() => router.push('/home')} className="btn-primary">
            ホームに戻る
          </button>
        </div>
      </div>
    );
  }

  const getScoreColor = (score: number, inverse = false) => {
    const normalizedScore = inverse ? 100 - score : score;
    if (normalizedScore >= 70) return 'text-success';
    if (normalizedScore >= 40) return 'text-accent-500';
    return 'text-danger';
  };

  const getScoreBarColor = (score: number, inverse = false) => {
    const normalizedScore = inverse ? 100 - score : score;
    if (normalizedScore >= 70) return 'from-success to-green-400';
    if (normalizedScore >= 40) return 'from-accent-500 to-accent-400';
    return 'from-danger to-red-400';
  };

  const scoreItems = [
    {
      label: '心身のストレス反応',
      value: result.stress_reaction_score,
      description: '身体や心の症状の程度',
      inverse: true,
    },
    {
      label: '仕事のストレス要因',
      value: result.job_stress_score,
      description: '仕事上のストレス原因',
      inverse: true,
    },
    {
      label: '周囲のサポート',
      value: result.support_score,
      description: '職場や家庭でのサポート',
      inverse: false,
    },
  ];

  return (
    <div className="page-container">
      <Header title="ストレスチェック結果" showHome />

      <main className="page-content">
        {/* Main Result Card */}
        <div className={`card p-8 mb-6 relative overflow-hidden animate-fade-in ${
          result.is_high_stress ? 'ring-2 ring-danger/30' : 'ring-2 ring-success/30'
        }`}>
          {/* Background decoration */}
          <div className={`absolute top-0 right-0 w-40 h-40 rounded-bl-full opacity-10 ${
            result.is_high_stress ? 'bg-danger' : 'bg-success'
          }`} />

          <div className="relative">
            <div className="flex items-center gap-4 mb-6">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ${
                result.is_high_stress
                  ? 'bg-gradient-to-br from-danger-light to-red-100'
                  : 'bg-gradient-to-br from-success-light to-green-100'
              }`}>
                {result.is_high_stress ? (
                  <IconFrown className="w-8 h-8 text-danger" />
                ) : (
                  <IconSmile className="w-8 h-8 text-success" />
                )}
              </div>
              <div>
                <h1 className="text-2xl font-bold text-sand-900">あなたのストレス状態</h1>
                <span className={`badge mt-1 ${result.is_high_stress ? 'badge-danger' : 'badge-success'}`}>
                  {result.is_high_stress ? '高ストレス' : '正常範囲'}
                </span>
              </div>
            </div>

            <div className="flex items-end gap-2 mb-6">
              <span className="text-6xl font-bold text-sand-900">{result.total_score}</span>
              <span className="text-xl text-sand-500 mb-2">/ 100</span>
            </div>

            {result.is_high_stress && (
              <div className="alert-warning">
                <IconAlertTriangle className="w-5 h-5 flex-shrink-0" />
                <div>
                  <p className="font-medium">産業医への相談を推奨します</p>
                  <p className="text-sm mt-1">ストレスが高い状態が続くと、心身の健康に影響を及ぼす可能性があります。</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Score Details */}
        <div className="grid gap-4 md:grid-cols-3 mb-6">
          {scoreItems.map((item, idx) => (
            <div
              key={item.label}
              className="card p-5 animate-fade-in-up"
              style={{ animationDelay: `${idx * 100}ms` }}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-sand-600">{item.label}</span>
                <IconActivity className={`w-4 h-4 ${getScoreColor(item.value, item.inverse)}`} />
              </div>
              <div className={`text-2xl font-bold mb-2 ${getScoreColor(item.value, item.inverse)}`}>
                {item.value.toFixed(1)}
              </div>
              <div className="progress h-2 mb-2">
                <div
                  className={`h-full bg-gradient-to-r ${getScoreBarColor(item.value, item.inverse)} rounded-full transition-all duration-500`}
                  style={{ width: `${Math.min(100, item.value)}%` }}
                />
              </div>
              <p className="text-xs text-sand-500">{item.description}</p>
            </div>
          ))}
        </div>

        {/* Advice Section */}
        <div className="card p-6 mb-6 animate-fade-in" style={{ animationDelay: '300ms' }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
              <IconHeart className="w-5 h-5 text-primary-600" />
            </div>
            <h2 className="font-bold text-sand-900">ストレス軽減のヒント</h2>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {[
              '十分な睡眠（7〜8時間）を心がけましょう',
              '適度な運動を日課に取り入れてみてください',
              '信頼できる人に悩みを相談してみましょう',
              '仕事と私生活のメリハリをつけましょう',
            ].map((tip, i) => (
              <div key={i} className="flex items-start gap-2 p-3 bg-sand-50 rounded-lg">
                <span className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-xs font-medium flex-shrink-0">
                  {i + 1}
                </span>
                <span className="text-sm text-sand-700">{tip}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => router.push('/chat')}
            className="btn-primary"
          >
            <IconChat className="w-4 h-4" />
            AIに相談する
          </button>
          <button
            onClick={() => router.push('/stress-check/history')}
            className="btn-secondary"
          >
            履歴を見る
          </button>
          <button
            onClick={() => router.push('/home')}
            className="btn-ghost"
          >
            ホームに戻る
          </button>
        </div>
      </main>
    </div>
  );
}
