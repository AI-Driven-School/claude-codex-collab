'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { lineApi, LineStatus, LineLinkCode } from '@/lib/api/line';
import { Header } from '@/components/ui/header';
import {
  IconCheckCircle, IconLoader, IconRefresh, IconAlertTriangle,
  IconChevronLeft, IconCopy
} from '@/components/ui/icons';

// LINE公式アカウントのURL（環境変数から取得または固定値）
const LINE_OFFICIAL_ACCOUNT_URL = process.env.NEXT_PUBLIC_LINE_OFFICIAL_ACCOUNT_URL || 'https://lin.ee/xxxxxx';

export default function LineLinkPage() {
  const router = useRouter();
  const [status, setStatus] = useState<LineStatus | null>(null);
  const [linkCode, setLinkCode] = useState<LineLinkCode | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [unlinking, setUnlinking] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await lineApi.getStatus();
      setStatus(data);
      if (data.link_code) {
        setLinkCode({ link_code: data.link_code, instruction: `LINEで「LINK:${data.link_code}」と送信` });
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/login');
      } else {
        setError('ステータスの取得に失敗しました');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCode = async () => {
    setGenerating(true);
    setError('');
    try {
      const data = await lineApi.generateLinkCode();
      setLinkCode(data);
      setStatus({ is_linked: false, link_code: data.link_code });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'コードの生成に失敗しました');
    } finally {
      setGenerating(false);
    }
  };

  const handleUnlink = async () => {
    if (!confirm('LINE連携を解除しますか？\n\n解除後はLINEからストレスチェックを受けられなくなります。')) {
      return;
    }
    setUnlinking(true);
    setError('');
    try {
      await lineApi.unlink();
      setStatus({ is_linked: false, link_code: null });
      setLinkCode(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || '連携解除に失敗しました');
    } finally {
      setUnlinking(false);
    }
  };

  const handleCopyCode = async () => {
    if (!linkCode) return;
    const textToCopy = `LINK:${linkCode.link_code}`;
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = textToCopy;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <IconLoader className="w-10 h-10 animate-spin text-primary-500 mx-auto mb-4" />
          <p className="text-sand-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Decorative background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="decorative-blob w-[400px] h-[400px] bg-[#06C755]/10 -top-40 -right-40" />
        <div className="decorative-blob w-[300px] h-[300px] bg-primary-100 bottom-20 -left-40" />
      </div>

      <Header title="LINE連携" showHome />

      <main className="page-content relative z-10">
        {/* Header Card */}
        <div className="card p-6 mb-6 animate-fade-in">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-[#06C755] flex items-center justify-center">
              <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63h2.386c.349 0 .63.285.63.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63.349 0 .631.285.631.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.281.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-sand-900">LINE連携</h1>
              <p className="text-sm text-sand-600">LINEからストレスチェックを受けられます</p>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="alert-danger mb-6 animate-fade-in-down">
            <IconAlertTriangle className="w-5 h-5 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Linked Status */}
        {status?.is_linked && (
          <div className="card p-6 mb-6 ring-2 ring-success/30 animate-scale-in">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-14 h-14 rounded-full bg-success-light flex items-center justify-center">
                <IconCheckCircle className="w-8 h-8 text-success" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-sand-900">連携済み</h2>
                <p className="text-sand-600">LINEアカウントと連携されています</p>
              </div>
            </div>

            <div className="p-4 bg-sand-50 rounded-xl mb-6">
              <h3 className="font-medium text-sand-800 mb-2">LINEでできること</h3>
              <ul className="space-y-2 text-sm text-sand-600">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-success" />
                  LINEからストレスチェックを受検
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-success" />
                  リマインド通知を受け取る
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-success" />
                  AIカウンセラーに相談
                </li>
              </ul>
            </div>

            <button
              onClick={handleUnlink}
              disabled={unlinking}
              className="btn-ghost text-danger hover:bg-danger-light"
            >
              {unlinking ? <IconLoader className="w-4 h-4 animate-spin" /> : null}
              {unlinking ? '解除中...' : '連携を解除'}
            </button>
          </div>
        )}

        {/* Not Linked - Generate Code */}
        {!status?.is_linked && (
          <>
            {/* Step 1: Add Friend */}
            <div className="card p-6 mb-6 animate-fade-in" style={{ animationDelay: '50ms' }}>
              <div className="flex items-center gap-3 mb-4">
                <span className="w-8 h-8 rounded-full bg-[#06C755] text-white flex items-center justify-center font-bold text-sm">1</span>
                <h2 className="font-bold text-sand-900">公式アカウントを友だち追加</h2>
              </div>

              <p className="text-sand-600 mb-4">
                まずLINE公式アカウントを友だち追加してください。
              </p>

              <a
                href={LINE_OFFICIAL_ACCOUNT_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary inline-flex items-center gap-2"
                style={{ backgroundColor: '#06C755' }}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63h2.386c.349 0 .63.285.63.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63.349 0 .631.285.631.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.281.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314" />
                </svg>
                友だち追加
              </a>
            </div>

            {/* Step 2: Generate Code */}
            <div className="card p-6 mb-6 animate-fade-in" style={{ animationDelay: '100ms' }}>
              <div className="flex items-center gap-3 mb-4">
                <span className="w-8 h-8 rounded-full bg-primary-500 text-white flex items-center justify-center font-bold text-sm">2</span>
                <h2 className="font-bold text-sand-900">連携コードを取得</h2>
              </div>

              {linkCode ? (
                <>
                  <p className="text-sand-600 mb-4">
                    以下のコードをLINEで送信してください:
                  </p>

                  <div className="p-4 bg-sand-800 rounded-xl mb-4">
                    <div className="flex items-center justify-between">
                      <code className="text-2xl font-mono font-bold text-white tracking-wider">
                        LINK:{linkCode.link_code}
                      </code>
                      <button
                        onClick={handleCopyCode}
                        className="p-2 rounded-lg hover:bg-sand-700 transition-colors text-sand-300 hover:text-white"
                        title="コピー"
                      >
                        {copied ? (
                          <IconCheckCircle className="w-5 h-5 text-success" />
                        ) : (
                          <IconCopy className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                    {copied && (
                      <p className="text-success text-xs mt-2">コピーしました!</p>
                    )}
                  </div>

                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
                    <p className="text-sm text-amber-800">
                      <strong>注意:</strong> このコードは一度しか使用できません。
                      連携後は別のコードが必要になります。
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <p className="text-sand-600 mb-4">
                    ボタンをクリックして連携コードを取得してください。
                  </p>

                  <button
                    onClick={handleGenerateCode}
                    disabled={generating}
                    className="btn-primary"
                  >
                    {generating ? <IconLoader className="w-4 h-4 animate-spin" /> : null}
                    {generating ? 'コード生成中...' : '連携コードを取得'}
                  </button>
                </>
              )}
            </div>

            {/* Step 3: Send Code */}
            <div className="card p-6 mb-6 animate-fade-in" style={{ animationDelay: '150ms' }}>
              <div className="flex items-center gap-3 mb-4">
                <span className="w-8 h-8 rounded-full bg-accent-500 text-white flex items-center justify-center font-bold text-sm">3</span>
                <h2 className="font-bold text-sand-900">LINEでコードを送信</h2>
              </div>

              <p className="text-sand-600 mb-4">
                友だち追加した公式アカウントに、上記の連携コードを送信してください。
              </p>

              <div className="p-4 bg-sand-50 rounded-xl">
                <p className="text-sm text-sand-700 leading-relaxed">
                  連携が完了すると、LINEから直接ストレスチェックを受けられるようになります。
                  リマインド通知もLINEで受け取れます。
                </p>
              </div>
            </div>

            {/* Refresh Button */}
            {linkCode && (
              <div className="text-center animate-fade-in" style={{ animationDelay: '200ms' }}>
                <button
                  onClick={loadStatus}
                  className="btn-ghost"
                >
                  <IconRefresh className="w-4 h-4" />
                  連携状態を確認
                </button>
              </div>
            )}
          </>
        )}

        {/* Back Button */}
        <div className="mt-8">
          <button
            onClick={() => router.push('/home')}
            className="btn-ghost"
          >
            <IconChevronLeft className="w-4 h-4" />
            ホームに戻る
          </button>
        </div>
      </main>
    </div>
  );
}
