'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/ui/header';
import {
  IconBrain,
  IconBuilding,
  IconTrendingUp,
  IconTrendingDown,
  IconAlertTriangle,
  IconLoader,
  IconDownload,
  IconUsers,
  IconCheckCircle,
  IconLightbulb,
} from '@/components/ui/icons';
import apiClient from '@/lib/api/client';

// 型定義
interface DepartmentScore {
  id: string;
  name: string;
  score: number;
  employee_count: number;
  risk_level: 'low' | 'medium' | 'high';
}

interface TrendData {
  month: string;
  score: number;
}

interface AIInsights {
  summary: string;
  risk_factors: string[];
  recommendations: string[];
}

interface OrgAnalysisData {
  organization_score: number;
  score_change: number;
  total_employees: number;
  response_rate: number;
  departments: DepartmentScore[];
  trends: TrendData[];
  ai_insights: AIInsights;
  generated_at: string;
}

export default function OrgAnalysisPage() {
  const router = useRouter();
  const [data, setData] = useState<OrgAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadAnalysis();
  }, []);

  const loadAnalysis = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get('/api/v1/admin/org-analysis');
      setData(response.data);
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('管理者権限が必要です');
      } else {
        setError(err.response?.data?.detail || '分析データの取得に失敗しました');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async () => {
    setGenerating(true);
    try {
      const response = await apiClient.post('/api/v1/admin/org-analysis/generate-report');
      // PDFダウンロード
      window.open(response.data.report_url, '_blank');
    } catch (err: any) {
      setError('レポート生成に失敗しました');
    } finally {
      setGenerating(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-red-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-green-500';
      default: return 'text-sand-500';
    }
  };

  const getRiskBg = (level: string) => {
    switch (level) {
      case 'high': return 'bg-red-50 border-red-200';
      case 'medium': return 'bg-yellow-50 border-yellow-200';
      case 'low': return 'bg-green-50 border-green-200';
      default: return 'bg-sand-50';
    }
  };

  const getRiskLabel = (level: string) => {
    switch (level) {
      case 'high': return '高リスク';
      case 'medium': return '中リスク';
      case 'low': return '低リスク';
      default: return '不明';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sand-50 to-white">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64" data-testid="org-analysis-loading">
            <IconLoader className="w-8 h-8 text-primary-500 animate-spin" />
            <span className="ml-3 text-sand-600">分析データを読み込み中...</span>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sand-50 to-white">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="alert-danger" data-testid="org-analysis-error">
            {error}
          </div>
        </main>
      </div>
    );
  }

  if (!data) return null;

  const highRiskCount = data.departments.filter(d => d.risk_level === 'high').length;

  return (
    <div className="min-h-screen bg-gradient-to-b from-sand-50 to-white">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {/* ヘッダー */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-primary-100 rounded-xl">
              <IconBrain className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-sand-900">組織分析AIダッシュボード</h1>
              <p className="text-sand-600">AIによる組織全体のストレス分析</p>
            </div>
          </div>
          <button
            onClick={handleExportPDF}
            disabled={generating}
            className="btn-primary flex items-center gap-2"
            data-testid="export-pdf-button"
          >
            {generating ? (
              <IconLoader className="w-4 h-4 animate-spin" />
            ) : (
              <IconDownload className="w-4 h-4" />
            )}
            PDFレポート出力
          </button>
        </div>

        {/* サマリーカード */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* 組織スコア */}
          <div className="card p-6" data-testid="org-score-card">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sand-600 font-medium">組織全体スコア</span>
              <IconBuilding className="w-5 h-5 text-sand-400" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-4xl font-bold text-sand-900">{data.organization_score}</span>
              <span className="text-sand-500 mb-1">/100</span>
            </div>
            <div className={`flex items-center mt-2 ${data.score_change >= 0 ? 'text-red-500' : 'text-green-500'}`}>
              {data.score_change >= 0 ? (
                <IconTrendingUp className="w-4 h-4 mr-1" />
              ) : (
                <IconTrendingDown className="w-4 h-4 mr-1" />
              )}
              <span className="text-sm font-medium">
                {data.score_change >= 0 ? '+' : ''}{data.score_change} 前月比
              </span>
            </div>
          </div>

          {/* 回答率 */}
          <div className="card p-6" data-testid="response-rate-card">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sand-600 font-medium">回答率</span>
              <IconUsers className="w-5 h-5 text-sand-400" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-4xl font-bold text-sand-900">{data.response_rate}</span>
              <span className="text-sand-500 mb-1">%</span>
            </div>
            <div className="text-sand-500 text-sm mt-2">
              {data.total_employees}名中
            </div>
          </div>

          {/* リスク部署 */}
          <div className="card p-6" data-testid="risk-dept-card">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sand-600 font-medium">高リスク部署</span>
              <IconAlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <div className="flex items-end gap-2">
              <span className="text-4xl font-bold text-red-500">{highRiskCount}</span>
              <span className="text-sand-500 mb-1">件</span>
            </div>
            <div className="text-sand-500 text-sm mt-2">
              全{data.departments.length}部署中
            </div>
          </div>
        </div>

        {/* AIインサイト */}
        <div className="card p-6 mb-8" data-testid="ai-insights-panel">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-primary-100 rounded-lg">
              <IconBrain className="w-5 h-5 text-primary-600" />
            </div>
            <h2 className="text-lg font-bold text-sand-900">AIインサイト</h2>
          </div>

          <p className="text-sand-700 mb-6 leading-relaxed">
            {data.ai_insights.summary}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* リスク要因 */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <IconAlertTriangle className="w-4 h-4 text-yellow-500" />
                <h3 className="font-semibold text-sand-800">リスク要因</h3>
              </div>
              <ul className="space-y-2">
                {data.ai_insights.risk_factors.map((factor, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sand-600">
                    <span className="text-yellow-500 mt-1">•</span>
                    {factor}
                  </li>
                ))}
              </ul>
            </div>

            {/* 改善提案 */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <IconLightbulb className="w-4 h-4 text-green-500" />
                <h3 className="font-semibold text-sand-800">改善提案</h3>
              </div>
              <ul className="space-y-2">
                {data.ai_insights.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sand-600">
                    <IconCheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* 部署別スコア & トレンド */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 部署別スコア */}
          <div className="card p-6" data-testid="department-list">
            <h2 className="text-lg font-bold text-sand-900 mb-4">部署別スコア</h2>
            <div className="space-y-3">
              {data.departments.map((dept) => (
                <div
                  key={dept.id}
                  className={`p-4 rounded-lg border ${getRiskBg(dept.risk_level)} cursor-pointer hover:shadow-md transition-shadow`}
                  data-testid={`department-row-${dept.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-sand-900">{dept.name}</div>
                      <div className="text-sm text-sand-500">{dept.employee_count}名</div>
                    </div>
                    <div className="text-right">
                      <div className={`text-2xl font-bold ${getRiskColor(dept.risk_level)}`}>
                        {dept.score}
                      </div>
                      <div className={`text-xs font-medium ${getRiskColor(dept.risk_level)}`}>
                        {getRiskLabel(dept.risk_level)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* トレンドグラフ */}
          <div className="card p-6" data-testid="trend-chart">
            <h2 className="text-lg font-bold text-sand-900 mb-4">スコア推移（過去6ヶ月）</h2>
            <div className="h-64 flex items-end justify-between gap-2">
              {data.trends.map((trend, idx) => {
                const height = Math.max(10, (trend.score / 100) * 100);
                const color = trend.score >= 70 ? 'bg-red-400' : trend.score >= 50 ? 'bg-yellow-400' : 'bg-green-400';
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center">
                    <div
                      className={`w-full ${color} rounded-t-lg transition-all hover:opacity-80`}
                      style={{ height: `${height}%` }}
                      title={`${trend.month}: ${trend.score}`}
                    />
                    <div className="text-xs text-sand-500 mt-2 truncate w-full text-center">
                      {trend.month.split('-')[1]}月
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-4 text-xs text-sand-400">
              <span>低ストレス</span>
              <span>高ストレス</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
