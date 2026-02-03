'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/ui/header';
import { IconFileText, IconChevronLeft, IconDownload, IconLoader } from '@/components/ui/icons';
import apiClient from '@/lib/api/client';
import { departmentApi, Department } from '@/lib/api/department';
import { userApi } from '@/lib/api/user';

export default function DashboardReportPage() {
  const router = useRouter();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadDepartments = async () => {
      try {
        const response = await departmentApi.getDepartments();
        setDepartments(response.departments);
        setSelectedDepartment(response.departments[0] || null);
      } catch (err: any) {
        setError(err.response?.data?.detail || '部署情報の取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };
    loadDepartments();
  }, []);

  const downloadPdf = async (url: string, filename: string) => {
    setDownloading(true);
    setError('');
    try {
      const response = await apiClient.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = filename;
      link.click();
      window.URL.revokeObjectURL(link.href);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'レポートのダウンロードに失敗しました');
    } finally {
      setDownloading(false);
    }
  };

  const handleDownloadGroupReport = async () => {
    const me = await userApi.getCurrentUser();
    await downloadPdf(
      `/api/v1/reports/company/${me.company_id}/group-analysis/pdf`,
      'group_analysis_report.pdf'
    );
  };

  const handleDownloadDepartmentReport = async () => {
    const me = await userApi.getCurrentUser();
    if (!selectedDepartment) {
      setError('部署を選択してください');
      return;
    }
    await downloadPdf(
      `/api/v1/reports/company/${me.company_id}/department/${encodeURIComponent(selectedDepartment.name)}/pdf`,
      `department_report_${selectedDepartment.name}.pdf`
    );
  };

  return (
    <div className="page-container">
      <Header title="詳細レポート" />

      <main className="page-content">
        <div className="card p-6 animate-fade-in mb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
              <IconFileText className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-sand-900">詳細レポート</h1>
              <p className="text-sm text-sand-600">集団分析・部署別分析のPDFをダウンロード</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="alert-danger mb-6 animate-fade-in-down">{error}</div>
        )}

        {loading ? (
          <div className="card p-8 text-center animate-fade-in">
            <IconLoader className="w-8 h-8 animate-spin text-primary-500 mx-auto mb-3" />
            <p className="text-sand-600">データを読み込んでいます...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-6 animate-fade-in-up">
              <h2 className="font-bold text-sand-900 mb-3">集団分析レポート</h2>
              <p className="text-sm text-sand-600 mb-5">
                最新期間の全社集計レポートを出力します。
              </p>
              <button
                onClick={handleDownloadGroupReport}
                disabled={downloading}
                className="btn-primary w-full"
              >
                <IconDownload className="w-4 h-4" />
                PDFをダウンロード
              </button>
            </div>

            <div className="card p-6 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
              <h2 className="font-bold text-sand-900 mb-3">部署別レポート</h2>
              <p className="text-sm text-sand-600 mb-4">
                選択した部署の最新期間レポートを出力します。
              </p>
              <select
                className="select mb-4"
                value={selectedDepartment?.id || ''}
                onChange={(e) => {
                  const dept = departments.find((d) => d.id === e.target.value) || null;
                  setSelectedDepartment(dept);
                }}
              >
                {departments.length === 0 && (
                  <option value="">部署がありません</option>
                )}
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
              <button
                onClick={handleDownloadDepartmentReport}
                disabled={downloading || !selectedDepartment}
                className="btn-secondary w-full"
              >
                <IconDownload className="w-4 h-4" />
                部署レポートをダウンロード
              </button>
            </div>
          </div>
        )}

        <div className="mt-6">
          <button
            onClick={() => router.push('/dashboard')}
            className="btn-ghost"
          >
            <IconChevronLeft className="w-4 h-4" />
            ダッシュボードに戻る
          </button>
        </div>
      </main>
    </div>
  );
}
