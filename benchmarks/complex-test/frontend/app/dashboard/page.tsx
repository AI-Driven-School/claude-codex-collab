'use client';

import { useEffect, useState, useCallback, useMemo, memo } from 'react';
import { useRouter } from 'next/navigation';
import { dashboardApi, DashboardResponse, DepartmentStat } from '@/lib/api/dashboard';
import { departmentApi, Department } from '@/lib/api/department';
import { userApi } from '@/lib/api/user';
import { Header } from '@/components/ui/header';
import {
  IconUsers, IconAlertTriangle, IconTrendingUp, IconBarChart,
  IconBuilding, IconBell, IconSparkles, IconDownload, IconClipboard,
  IconFileText, IconLoader, IconGrid, IconList
} from '@/components/ui/icons';
import { DepartmentHeatmap } from '@/components/dashboard/DepartmentHeatmap';

// Memoized stat card component
const StatCard = memo(function StatCard({
  label,
  value,
  icon: Icon,
  color,
  delay
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  delay: number;
}) {
  const colorClasses = useMemo(() => {
    switch (color) {
      case 'primary':
        return 'bg-gradient-to-br from-primary-100 to-primary-200 text-primary-600';
      case 'danger':
        return 'bg-gradient-to-br from-danger-light to-red-100 text-danger';
      case 'success':
        return 'bg-gradient-to-br from-success-light to-green-100 text-success';
      default:
        return 'bg-gradient-to-br from-accent-100 to-accent-200 text-accent-600';
    }
  }, [color]);

  return (
    <div
      className="stat-card animate-fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${colorClasses}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
});

// Memoized department list item
const DepartmentListItem = memo(function DepartmentListItem({
  dept,
  delay
}: {
  dept: DepartmentStat;
  delay: number;
}) {
  const isHighRisk = dept.average_score > 70;
  const isMediumRisk = dept.average_score > 50;

  const scoreColorClass = useMemo(() => {
    if (isHighRisk) return 'text-danger';
    if (isMediumRisk) return 'text-accent-500';
    return 'text-success';
  }, [isHighRisk, isMediumRisk]);

  const barColorClass = useMemo(() => {
    if (isHighRisk) return 'bg-danger';
    if (isMediumRisk) return 'bg-accent-400';
    return 'bg-success';
  }, [isHighRisk, isMediumRisk]);

  return (
    <div
      className="p-4 bg-sand-50 rounded-xl animate-fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-sand-800">{dept.department_name}</span>
        <div className="flex items-center gap-2">
          {dept.high_stress_count > 0 && (
            <span className="badge badge-danger">{dept.high_stress_count}名高ストレス</span>
          )}
          <span className={`text-lg font-bold ${scoreColorClass}`}>
            {dept.average_score.toFixed(1)}
          </span>
        </div>
      </div>
      <div className="progress h-2">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColorClass}`}
          style={{ width: `${Math.min(100, dept.average_score)}%` }}
        />
      </div>
      <div className="mt-2 text-xs text-sand-500">
        従業員数: {dept.employee_count}名
      </div>
    </div>
  );
});

// Memoized quick action card
const QuickActionCard = memo(function QuickActionCard({
  href,
  icon: Icon,
  iconColorClass,
  title,
  description,
  delay
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  iconColorClass: string;
  title: string;
  description: string;
  delay: number;
}) {
  return (
    <a href={href} className="card-interactive p-5 group animate-fade-in-up" style={{ animationDelay: `${delay}ms` }}>
      <div className={`w-12 h-12 rounded-xl ${iconColorClass} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="font-bold text-sand-900">{title}</h3>
      <p className="text-sm text-sand-600 mt-1">{description}</p>
    </a>
  );
});

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string>('');
  const [companyId, setCompanyId] = useState<string>('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'list' | 'heatmap'>('heatmap');

  const loadDashboardData = useCallback(async (compId: string, deptId?: string) => {
    try {
      const response = await dashboardApi.getCompanyDashboard(compId, {
        departmentId: deptId || undefined,
      });
      setData(response);
      setError('');
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('アクセス権限がありません');
        router.push('/home');
      } else if (err.response?.status === 401) {
        router.push('/login');
      } else {
        setError(err.response?.data?.detail || 'データの取得に失敗しました');
      }
    }
  }, [router]);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const userInfo = await userApi.getCurrentUser();
        setCompanyId(userInfo.company_id);

        try {
          const deptResponse = await departmentApi.getDepartments();
          setDepartments(deptResponse.departments);
        } catch {
          setDepartments([]);
        }

        await loadDashboardData(userInfo.company_id);
      } catch (err: any) {
        if (err.response?.status === 403) {
          setError('アクセス権限がありません');
          router.push('/home');
        } else if (err.response?.status === 401) {
          router.push('/login');
        } else {
          setError(err.response?.data?.detail || 'データの取得に失敗しました');
        }
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, [router, loadDashboardData]);

  const handleDepartmentChange = useCallback(async (departmentId: string) => {
    setSelectedDepartmentId(departmentId);
    setLoading(true);
    await loadDashboardData(companyId, departmentId);
    setLoading(false);
  }, [companyId, loadDashboardData]);

  const handleExportCSV = useCallback(() => {
    if (!data) return;
    const csv = 'data:text/csv;charset=utf-8,部署,平均スコア\n全体,' + data.stats.average_stress_score;
    const link = document.createElement('a');
    link.href = csv;
    link.download = 'dashboard.csv';
    link.click();
  }, [data]);

  // Memoize stat cards configuration
  const statCards = useMemo(() => {
    if (!data) return [];
    return [
      {
        label: '総従業員数',
        value: data.stats.total_employees,
        icon: IconUsers,
        color: 'primary',
      },
      {
        label: '高ストレス者数',
        value: data.stats.high_stress_count,
        icon: IconAlertTriangle,
        color: data.stats.high_stress_count > 0 ? 'danger' : 'success',
      },
      {
        label: '受検率',
        value: `${data.stats.stress_check_completion_rate.toFixed(1)}%`,
        icon: IconTrendingUp,
        color: data.stats.stress_check_completion_rate >= 80 ? 'success' : 'accent',
      },
      {
        label: '平均スコア',
        value: data.stats.average_stress_score.toFixed(1),
        icon: IconBarChart,
        color: 'primary',
      },
    ];
  }, [data]);

  // Memoize quick actions
  const quickActions = useMemo(() => [
    {
      href: '/dashboard/stress-check',
      icon: IconClipboard,
      iconColorClass: 'bg-gradient-to-br from-primary-100 to-primary-200 text-primary-600',
      title: 'ストレスチェック管理',
      description: '未受検者の確認・リマインド',
    },
    {
      href: '/dashboard/report',
      icon: IconFileText,
      iconColorClass: 'bg-gradient-to-br from-accent-100 to-accent-200 text-accent-600',
      title: '詳細レポート',
      description: '分析レポートの確認',
    },
    {
      href: '/admin/csv-import',
      icon: IconUsers,
      iconColorClass: 'bg-gradient-to-br from-success-light to-green-100 text-success',
      title: '従業員管理',
      description: 'CSV一括登録・管理',
    },
    {
      href: '/admin/departments',
      icon: IconBuilding,
      iconColorClass: 'bg-gradient-to-br from-primary-100 to-primary-200 text-primary-600',
      title: '部署管理',
      description: '部署の追加・編集・削除',
    },
  ], []);

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <IconLoader className="w-10 h-10 animate-spin text-primary-500 mx-auto mb-4" />
          <p className="text-sand-600">ダッシュボードを読み込んでいます...</p>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="card p-8 text-center max-w-md">
          <div className="w-16 h-16 rounded-full bg-danger-light flex items-center justify-center mx-auto mb-4">
            <IconAlertTriangle className="w-8 h-8 text-danger" />
          </div>
          <h2 className="text-lg font-bold text-sand-900 mb-2">エラー</h2>
          <p className="text-sand-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="card p-8 text-center max-w-md">
          <div className="w-16 h-16 rounded-full bg-sand-100 flex items-center justify-center mx-auto mb-4">
            <IconBarChart className="w-8 h-8 text-sand-400" />
          </div>
          <h2 className="text-lg font-bold text-sand-900 mb-2">データがありません</h2>
          <p className="text-sand-600">まだデータが登録されていません</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Decorative background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="decorative-blob w-[500px] h-[500px] bg-primary-100 -top-40 -right-40" />
        <div className="decorative-blob w-[400px] h-[400px] bg-accent-100 bottom-20 -left-40" />
      </div>

      <Header title="管理者ダッシュボード" />

      <main className="page-content relative z-10">
        {/* Filters */}
        <div className="card p-4 mb-6 flex flex-wrap gap-4 items-center justify-between animate-fade-in">
          <div className="flex gap-4">
            <select className="select min-w-[140px]">
              <option>全ての期間</option>
              <option>過去30日</option>
              <option>過去3ヶ月</option>
              <option>過去1年</option>
            </select>
            <select
              className="select min-w-[160px]"
              value={selectedDepartmentId}
              onChange={(e) => handleDepartmentChange(e.target.value)}
            >
              <option value="">全ての部署</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>{dept.name}</option>
              ))}
            </select>
          </div>
          <button onClick={handleExportCSV} className="btn-secondary">
            <IconDownload className="w-4 h-4" />
            CSVエクスポート
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {statCards.map((stat, idx) => (
            <StatCard
              key={stat.label}
              label={stat.label}
              value={stat.value}
              icon={stat.icon}
              color={stat.color}
              delay={idx * 50}
            />
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-6">
          {/* Department Stats */}
          <div className="lg:col-span-2 card p-6 animate-fade-in" style={{ animationDelay: '200ms' }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-sand-900 flex items-center gap-2">
                <IconBuilding className="w-5 h-5 text-primary-500" />
                部署別ストレス状況
              </h2>
              {/* 表示切り替えボタン */}
              <div className="flex items-center gap-1 bg-sand-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('heatmap')}
                  className={`p-2 rounded-md transition-all ${
                    viewMode === 'heatmap'
                      ? 'bg-white shadow-soft text-primary-600'
                      : 'text-sand-500 hover:text-sand-700'
                  }`}
                  title="ヒートマップ表示"
                >
                  <IconGrid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-md transition-all ${
                    viewMode === 'list'
                      ? 'bg-white shadow-soft text-primary-600'
                      : 'text-sand-500 hover:text-sand-700'
                  }`}
                  title="リスト表示"
                >
                  <IconList className="w-4 h-4" />
                </button>
              </div>
            </div>

            {viewMode === 'heatmap' ? (
              <DepartmentHeatmap departments={data.department_stats} />
            ) : (
              <>
                {data.department_stats.length === 0 ? (
                  <div className="text-center py-8 text-sand-500">部署データがありません</div>
                ) : (
                  <div className="space-y-3">
                    {data.department_stats.map((dept, idx) => (
                      <DepartmentListItem
                        key={dept.department_name}
                        dept={dept}
                        delay={300 + idx * 50}
                      />
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Alerts */}
          <div className="card p-6 animate-fade-in" style={{ animationDelay: '250ms' }}>
            <h2 className="font-bold text-sand-900 flex items-center gap-2 mb-4">
              <IconBell className="w-5 h-5 text-accent-500" />
              アラート
            </h2>

            {data.alerts.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-success-light flex items-center justify-center mx-auto mb-3">
                  <IconBell className="w-6 h-6 text-success" />
                </div>
                <p className="text-sand-600">アラートはありません</p>
              </div>
            ) : (
              <div className="space-y-3">
                {data.alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-3 rounded-lg border ${
                      alert.alert_level === 'critical' ? 'bg-danger-light border-danger/20' :
                      alert.alert_level === 'warning' ? 'bg-warning-light border-warning/20' :
                      'bg-info-light border-info/20'
                    }`}
                  >
                    <div className="font-medium text-sm">{alert.department_name}</div>
                    <div className="text-xs mt-1 opacity-80">{alert.message}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* AI Recommendations */}
        <div className="card p-6 mb-6 animate-fade-in" style={{ animationDelay: '300ms' }}>
          <h2 className="font-bold text-sand-900 flex items-center gap-2 mb-4">
            <IconSparkles className="w-5 h-5 text-primary-500" />
            AI改善提案
          </h2>

          {data.recommendations.length === 0 ? (
            <div className="text-center py-8 text-sand-500">
              提案はありません
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {data.recommendations.map((rec, idx) => (
                <div
                  key={rec.id}
                  className="p-4 bg-gradient-to-br from-primary-50 to-white rounded-xl border border-primary-100 animate-fade-in-up"
                  style={{ animationDelay: `${350 + idx * 50}ms` }}
                >
                  <h3 className="font-medium text-sand-800 mb-1">{rec.title}</h3>
                  <p className="text-sm text-sand-600">{rec.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-4">
          {quickActions.map((action, idx) => (
            <QuickActionCard
              key={action.href}
              href={action.href}
              icon={action.icon}
              iconColorClass={action.iconColorClass}
              title={action.title}
              description={action.description}
              delay={400 + idx * 50}
            />
          ))}
        </div>
      </main>
    </div>
  );
}
