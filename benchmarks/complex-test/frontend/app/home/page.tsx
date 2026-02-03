'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { userApi } from '@/lib/api/user';
import { Header } from '@/components/ui/header';
import { IconClipboard, IconHistory, IconChat, IconChevronRight, IconHeart, IconSparkles, IconLink } from '@/components/ui/icons';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await userApi.getCurrentUser();
      } catch {
        router.push('/login');
      }
    };
    checkAuth();
  }, [router]);

  const menuItems = [
    {
      href: '/stress-check',
      icon: IconClipboard,
      title: 'ストレスチェック',
      description: '57項目のストレスチェックを受検して、今の状態を把握しましょう',
      color: 'primary',
      badge: '推奨',
    },
    {
      href: '/stress-check/history',
      icon: IconHistory,
      title: '受検履歴',
      description: '過去のストレスチェック結果を確認できます',
      color: 'accent',
    },
    {
      href: '/chat',
      icon: IconChat,
      title: 'AIカウンセリング',
      description: 'AIアシスタントと会話してメンタルヘルスをチェック',
      color: 'primary',
      badge: 'AI',
    },
    {
      href: '/home/line-link',
      icon: IconLink,
      title: 'LINE連携',
      description: 'LINEと連携してスマホから手軽にチェック',
      color: 'accent',
      badge: 'LINE',
    },
  ];

  return (
    <div className="page-container">
      {/* Decorative background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="decorative-blob w-96 h-96 bg-primary-200 top-20 -right-20" />
        <div className="decorative-blob w-80 h-80 bg-accent-200 bottom-40 -left-20" />
      </div>

      <Header />

      <main className="page-content relative z-10">
        {/* Welcome Section */}
        <div className="mb-10 animate-fade-in">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-400 to-accent-500 flex items-center justify-center">
              <IconHeart className="w-5 h-5 text-white" />
            </div>
            <span className="text-sm font-medium text-accent-600 bg-accent-100 px-3 py-1 rounded-full">
              ようこそ
            </span>
          </div>
          <h1 className="text-3xl font-bold text-sand-900 mb-2">
            今日も<span className="gradient-text">お疲れさまです</span>
          </h1>
          <p className="text-sand-600 max-w-md">
            こころの健康は、毎日の積み重ねから。今日も自分と向き合う時間を大切にしましょう。
          </p>
        </div>

        {/* Menu Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
          {menuItems.map((item, index) => (
            <a
              key={item.href}
              href={item.href}
              className="card-interactive group p-6 animate-fade-in-up"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                  item.color === 'primary'
                    ? 'bg-gradient-to-br from-primary-100 to-primary-200 text-primary-600'
                    : 'bg-gradient-to-br from-accent-100 to-accent-200 text-accent-600'
                }`}>
                  <item.icon className="w-7 h-7" />
                </div>
                {item.badge && (
                  <span className={`badge ${item.badge === 'AI' ? 'badge-primary' : 'badge-accent'}`}>
                    {item.badge === 'AI' && <IconSparkles className="w-3 h-3 mr-1" />}
                    {item.badge}
                  </span>
                )}
              </div>

              <h2 className="text-xl font-bold text-sand-900 mb-2 group-hover:text-primary-600 transition-colors">
                {item.title}
              </h2>
              <p className="text-sand-600 text-sm leading-relaxed mb-4">
                {item.description}
              </p>

              <div className="flex items-center text-primary-600 font-medium text-sm">
                <span>はじめる</span>
                <IconChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
              </div>
            </a>
          ))}
        </div>

        {/* Quick Tips Section */}
        <div className="card p-6 animate-fade-in" style={{ animationDelay: '400ms' }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
              <IconSparkles className="w-5 h-5 text-primary-600" />
            </div>
            <h3 className="font-bold text-sand-900">今日のワンポイント</h3>
          </div>
          <p className="text-sand-700 leading-relaxed">
            ストレスを感じたら、まずは深呼吸を3回してみましょう。
            吸うときは4秒、止めて4秒、吐くときは6秒を意識すると、自律神経が整いやすくなります。
          </p>
        </div>
      </main>
    </div>
  );
}
