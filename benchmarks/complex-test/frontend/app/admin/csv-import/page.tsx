'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api/client';
import { Header } from '@/components/ui/header';
import {
  IconUpload, IconDownload, IconCheckCircle, IconXCircle, IconLoader,
  IconUsers, IconFileText, IconRefresh, IconAlertTriangle
} from '@/components/ui/icons';

interface CSVPreviewRow {
  row_number: number;
  email: string;
  name: string;
  employee_id: string;
  department: string;
  is_valid: boolean;
  errors: string[];
}

interface CSVPreviewResponse {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  duplicate_in_csv: number;
  duplicate_in_db: number;
  preview_data: CSVPreviewRow[];
  can_import: boolean;
}

interface CSVImportResult {
  success: boolean;
  total_rows: number;
  imported_count: number;
  skipped_count: number;
  message: string;
}

export default function CSVImportPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CSVPreviewResponse | null>(null);
  const [result, setResult] = useState<CSVImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('CSVファイルのみアップロード可能です');
        return;
      }
      setFile(selectedFile);
      setPreview(null);
      setResult(null);
      setError('');
    }
  };

  const handlePreview = async () => {
    if (!file) return;

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post('/api/v1/admin/csv/preview', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setPreview(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'プレビューの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (skipErrors: boolean = false) => {
    if (!file) return;

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post(
        `/api/v1/admin/csv/import?skip_errors=${skipErrors}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      setResult(response.data);
      if (response.data.success) {
        setPreview(null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'インポートに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await apiClient.get('/api/v1/admin/csv/template', {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'employee_template.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('テンプレートのダウンロードに失敗しました');
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="page-container">
      <Header title="CSV一括登録" />

      <main className="page-content">
        {/* Header Card */}
        <div className="card p-6 mb-6 animate-fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
                <IconUsers className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-sand-900">従業員CSV一括登録</h1>
                <p className="text-sm text-sand-600">CSVファイルから従業員を一括で登録</p>
              </div>
            </div>
            <button onClick={() => router.push('/dashboard')} className="btn-ghost">
              ダッシュボードに戻る
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="alert-danger mb-6 animate-fade-in-down" data-testid="csv-import-error">
            <IconAlertTriangle className="w-5 h-5 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Import Result */}
        {result && (
          <div className={`card p-6 mb-6 animate-scale-in ${result.success ? 'ring-2 ring-success/30' : 'ring-2 ring-warning/30'}`}>
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                result.success ? 'bg-success-light' : 'bg-warning-light'
              }`}>
                {result.success ? (
                  <IconCheckCircle className="w-6 h-6 text-success" />
                ) : (
                  <IconAlertTriangle className="w-6 h-6 text-warning" />
                )}
              </div>
              <div className="flex-1">
                <h2 className="font-bold text-sand-900 mb-2">インポート結果</h2>
                <p className="text-sand-700 mb-4">{result.message}</p>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="p-3 bg-sand-50 rounded-lg">
                    <div className="text-sand-500">総行数</div>
                    <div className="text-xl font-bold text-sand-900">{result.total_rows}</div>
                  </div>
                  <div className="p-3 bg-success-light rounded-lg">
                    <div className="text-success-dark">成功</div>
                    <div className="text-xl font-bold text-success">{result.imported_count}</div>
                  </div>
                  <div className="p-3 bg-warning-light rounded-lg">
                    <div className="text-warning-dark">スキップ</div>
                    <div className="text-xl font-bold text-warning">{result.skipped_count}</div>
                  </div>
                </div>
                {result.success && (
                  <button onClick={handleReset} className="btn-primary mt-4">
                    <IconRefresh className="w-4 h-4" />
                    新しいファイルをアップロード
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* CSV Format Guide */}
        <div className="card p-6 mb-6 animate-fade-in" style={{ animationDelay: '50ms' }}>
          <div className="flex items-center gap-3 mb-4">
            <IconFileText className="w-5 h-5 text-primary-500" />
            <h2 className="font-bold text-sand-900">CSVフォーマット</h2>
          </div>
          <p className="text-sand-600 mb-4">以下の形式でCSVファイルを作成してください:</p>
          <div className="bg-sand-800 text-sand-100 p-4 rounded-xl font-mono text-sm overflow-x-auto mb-4">
            <div className="text-sand-400">// ヘッダー行</div>
            <div>email,name,employee_id,department</div>
            <div className="text-sand-400 mt-2">// データ行</div>
            <div>user@example.com,山田太郎,EMP001,営業部</div>
          </div>
          <button
            onClick={handleDownloadTemplate}
            className="btn-secondary"
            data-testid="csv-template-download"
          >
            <IconDownload className="w-4 h-4" />
            テンプレートをダウンロード
          </button>
        </div>

        {/* File Upload */}
        <div className="card p-6 mb-6 animate-fade-in" style={{ animationDelay: '100ms' }}>
          <div className="flex items-center gap-3 mb-4">
            <IconUpload className="w-5 h-5 text-primary-500" />
            <h2 className="font-bold text-sand-900">ファイルアップロード</h2>
          </div>

          <div className="border-2 border-dashed border-sand-200 rounded-xl p-8 text-center hover:border-primary-300 transition-colors">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
              id="csv-upload"
              data-testid="csv-file-input"
            />
            <label htmlFor="csv-upload" className="cursor-pointer" data-testid="csv-file-dropzone">
              <div className="w-16 h-16 rounded-2xl bg-sand-100 flex items-center justify-center mx-auto mb-4">
                <IconUpload className="w-8 h-8 text-sand-400" />
              </div>
              {file ? (
                <div data-testid="csv-file-selected">
                  <p className="font-medium text-sand-900" data-testid="csv-file-name">{file.name}</p>
                  <p className="text-sm text-sand-500 mt-1">クリックして別のファイルを選択</p>
                </div>
              ) : (
                <div data-testid="csv-file-empty">
                  <p className="font-medium text-sand-700">クリックしてCSVファイルを選択</p>
                  <p className="text-sm text-sand-500 mt-1">またはドラッグ&ドロップ</p>
                </div>
              )}
            </label>
          </div>

          {file && (
            <div className="mt-4 flex gap-3">
              <button
                onClick={handlePreview}
                disabled={loading}
                className="btn-primary"
                data-testid="csv-preview-button"
              >
                {loading ? <IconLoader className="w-4 h-4 animate-spin" /> : null}
                {loading ? '処理中...' : 'プレビュー'}
              </button>
              <button onClick={handleReset} className="btn-secondary" data-testid="csv-reset-button">
                リセット
              </button>
            </div>
          )}
        </div>

        {/* Preview Table */}
        {preview && (
          <div className="card p-6 animate-fade-in">
            <h2 className="font-bold text-sand-900 mb-4">プレビュー</h2>

            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
              <div className="p-3 bg-sand-50 rounded-xl text-center">
                <div className="text-xs text-sand-500 mb-1">総行数</div>
                <div className="text-xl font-bold text-sand-900">{preview.total_rows}</div>
              </div>
              <div className="p-3 bg-success-light rounded-xl text-center">
                <div className="text-xs text-success-dark mb-1">有効</div>
                <div className="text-xl font-bold text-success">{preview.valid_rows}</div>
              </div>
              <div className="p-3 bg-danger-light rounded-xl text-center">
                <div className="text-xs text-danger-dark mb-1">エラー</div>
                <div className="text-xl font-bold text-danger">{preview.invalid_rows}</div>
              </div>
              <div className="p-3 bg-warning-light rounded-xl text-center">
                <div className="text-xs text-warning-dark mb-1">CSV内重複</div>
                <div className="text-xl font-bold text-warning">{preview.duplicate_in_csv}</div>
              </div>
              <div className="p-3 bg-accent-100 rounded-xl text-center">
                <div className="text-xs text-accent-700 mb-1">DB重複</div>
                <div className="text-xl font-bold text-accent-600">{preview.duplicate_in_db}</div>
              </div>
            </div>

            {/* Data Table */}
            <div className="table-container mb-6">
              <table className="table">
                <thead>
                  <tr>
                    <th>行</th>
                    <th>状態</th>
                    <th>メール</th>
                    <th>名前</th>
                    <th>社員ID</th>
                    <th>部署</th>
                    <th>エラー</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.preview_data.map((row) => (
                    <tr key={row.row_number} className={row.is_valid ? '' : 'bg-danger-light/50'}>
                      <td>{row.row_number}</td>
                      <td>
                        {row.is_valid ? (
                          <span className="badge badge-success">OK</span>
                        ) : (
                          <span className="badge badge-danger">NG</span>
                        )}
                      </td>
                      <td className="font-mono text-xs">{row.email}</td>
                      <td>{row.name}</td>
                      <td className="font-mono text-xs">{row.employee_id}</td>
                      <td>{row.department}</td>
                      <td className="text-danger text-xs">{row.errors.join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Import Actions */}
            <div className="flex flex-wrap gap-3">
              {preview.can_import && (
                <>
                  <button
                    onClick={() => handleImport(false)}
                    disabled={loading || preview.invalid_rows > 0}
                    className="btn-primary"
                  >
                    {loading ? <IconLoader className="w-4 h-4 animate-spin" /> : null}
                    {loading ? '処理中...' : 'インポート実行'}
                  </button>
                  {preview.invalid_rows > 0 && (
                    <button
                      onClick={() => handleImport(true)}
                      disabled={loading}
                      className="btn-accent"
                    >
                      {loading ? <IconLoader className="w-4 h-4 animate-spin" /> : null}
                      {loading ? '処理中...' : 'エラー行をスキップしてインポート'}
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
