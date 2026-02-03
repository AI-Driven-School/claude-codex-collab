'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { chatApi, ChatResponse, ChatHistoryMessage } from '@/lib/api/chat';
import { IconSend, IconTrash, IconBrain, IconHome, IconSparkles, IconLoader } from '@/components/ui/icons';

interface Message {
  id?: string;
  role: 'user' | 'ai';
  content: string;
  sentiment_score?: number;
}

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const loadChatHistory = async () => {
      try {
        const response = await chatApi.getHistory(100, 0);
        const loadedMessages: Message[] = response.messages.map((msg: ChatHistoryMessage) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          sentiment_score: msg.sentiment_score,
        }));
        setMessages(loadedMessages);
      } catch (err: any) {
        console.warn('チャット履歴の取得に失敗しました。', err);
      } finally {
        setLoading(false);
      }
    };

    loadChatHistory();
  }, []);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || sending) return;

    if (input.length > 1000) {
      setError('メッセージは1000文字以内で入力してください');
      return;
    }

    const userMessage = input.trim();
    setInput('');
    setError('');
    setSending(true);

    const newUserMessage: Message = { role: 'user', content: userMessage };
    const updatedMessages = [...messages, newUserMessage];
    setMessages(updatedMessages);

    try {
      // まずAI応答を取得（成功時のみDB保存）
      const response: ChatResponse = await chatApi.sendMessage({ content: userMessage });

      const aiMessage: Message = {
        role: 'ai',
        content: response.message,
        sentiment_score: response.sentiment_score,
      };

      // 送信成功後にユーザーメッセージとAI応答を保存
      await chatApi.saveMessage({ role: 'user', content: userMessage });
      await chatApi.saveMessage({
        role: 'ai',
        content: response.message,
        sentiment_score: response.sentiment_score,
      });

      const newMessages = [...updatedMessages, aiMessage];
      setMessages(newMessages);
    } catch (err: any) {
      // 失敗時はUIのメッセージも元に戻す
      setMessages(messages);
      if (!err.response) {
        setError('ネットワークエラーが発生しました');
      } else if (err.response?.status === 429) {
        setError('送信回数の上限に達しました');
      } else if (err.response?.status === 400 && err.response?.data?.detail?.includes('不適切な内容')) {
        setError('不適切な内容が検出されました');
      } else {
        setError(err.response?.data?.detail || 'メッセージの送信に失敗しました');
      }
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleClearHistory = async () => {
    if (!confirm('チャット履歴を全て削除しますか？')) return;

    try {
      await chatApi.deleteHistory();
      setMessages([]);
    } catch (err: any) {
      setError('履歴の削除に失敗しました');
    }
  };

  const getSentimentEmoji = (score: number) => {
    if (score >= 0.3) return '😊';
    if (score >= -0.3) return '😐';
    return '😔';
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-sand-50 via-white to-primary-50/30">
      {/* Header */}
      <header className="header flex-shrink-0">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-glow">
              <IconBrain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-sand-900">AIカウンセリング</h1>
              <p className="text-xs text-sand-500">いつでもあなたのそばに</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={handleClearHistory}
                className="icon-btn text-danger hover:text-danger-dark hover:bg-danger-light"
                aria-label="履歴を削除"
              >
                <IconTrash className="w-5 h-5" />
              </button>
            )}
            <button
              onClick={() => router.push('/home')}
              className="icon-btn"
              aria-label="ホームに戻る"
            >
              <IconHome className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <IconLoader className="w-8 h-8 animate-spin text-primary-500 mx-auto mb-3" />
                <p className="text-sand-500">履歴を読み込んでいます...</p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center animate-fade-in">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center mb-6">
                <IconSparkles className="w-10 h-10 text-primary-600" />
              </div>
              <h2 className="text-xl font-bold text-sand-900 mb-2">
                こんにちは！
              </h2>
              <p className="text-sand-600 max-w-sm">
                私はAIアシスタントです。<br />
                今日の気分や悩みを気軽に話してみてください。
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {['今日は疲れた', '最近眠れない', 'ストレスを感じる'].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setInput(prompt)}
                    className="px-4 py-2 bg-white border border-sand-200 rounded-full text-sm text-sand-700 hover:border-primary-300 hover:bg-primary-50 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={msg.id || idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                >
                  {msg.role === 'ai' && (
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center mr-3 flex-shrink-0 mt-1">
                      <IconBrain className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div
                    className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.role === 'ai' && msg.sentiment_score !== undefined && (
                      <div className="mt-2 pt-2 border-t border-sand-100 flex items-center gap-2 text-xs text-sand-500">
                        <span>{getSentimentEmoji(msg.sentiment_score)}</span>
                        <span>感情スコア: {msg.sentiment_score.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {sending && (
                <div className="flex justify-start animate-fade-in">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center mr-3 flex-shrink-0">
                    <IconBrain className="w-4 h-4 text-white" />
                  </div>
                  <div className="chat-bubble-ai">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-primary-400 rounded-full animate-pulse" />
                        <span className="w-2 h-2 bg-primary-400 rounded-full animate-pulse delay-100" />
                        <span className="w-2 h-2 bg-primary-400 rounded-full animate-pulse delay-200" />
                      </div>
                      <span className="text-sand-500 text-sm">考えています...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex-shrink-0 px-4">
          <div className="max-w-4xl mx-auto">
            <div className={`${
              error.includes('不適切') ? 'alert-warning' : 'alert-danger'
            } animate-fade-in-down`}>
              <span>{error}</span>
            </div>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="flex-shrink-0 border-t border-sand-100 bg-white/80 backdrop-blur-lg">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="メッセージを入力..."
                className="input pr-12"
                maxLength={1000}
                disabled={sending}
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-sand-400">
                {input.length}/1000
              </span>
            </div>
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="btn-primary h-12 w-12 p-0 flex-shrink-0"
              aria-label="送信"
            >
              {sending ? (
                <IconLoader className="w-5 h-5 animate-spin" />
              ) : (
                <IconSend className="w-5 h-5" />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
