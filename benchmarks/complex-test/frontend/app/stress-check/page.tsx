'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { stressCheckApi, StressCheckQuestion } from '@/lib/api/stress-check';
import { Header } from '@/components/ui/header';
import { IconClipboard, IconCheckCircle, IconLoader, IconChevronLeft, IconChevronRight } from '@/components/ui/icons';

export default function StressCheckPage() {
  const router = useRouter();
  const [questions, setQuestions] = useState<StressCheckQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [currentSection, setCurrentSection] = useState(0);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const sections = [
    { title: 'ストレスの原因', start: 0, end: 17 },
    { title: '心身の反応', start: 17, end: 46 },
    { title: '周囲のサポート', start: 46, end: 57 },
  ];

  const currentSectionData = sections[currentSection];
  const sectionQuestions = questions.slice(currentSectionData.start, currentSectionData.end);
  const answeredInSection = sectionQuestions.filter(q => answers[q.id] !== undefined).length;
  const totalAnswered = Object.keys(answers).length;

  const debouncedSave = useCallback(async (answersToSave: Record<string, number>) => {
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(async () => {
      if (Object.keys(answersToSave).length > 0) {
        try {
          await stressCheckApi.saveDraft(answersToSave);
        } catch {}
      }
    }, 1000);
  }, []);

  useEffect(() => {
    const loadQuestions = async () => {
      try {
        const response = await stressCheckApi.getQuestions();
        setQuestions(response.questions);

        if (response.already_taken) {
          setInfo(response.message || 'この期間は既に受検済みです。');
          setError('');
        }

        try {
          const draftResponse = await stressCheckApi.getDraft();
          if (draftResponse.answers && Object.keys(draftResponse.answers).length > 0) {
            setAnswers(draftResponse.answers);
          }
        } catch {}
      } catch (err: any) {
        if (!err.response) {
          setError('ネットワークエラーが発生しました');
        } else if (err.response?.status === 400 && err.response?.data?.detail?.includes('既に受検済み')) {
          setInfo('この期間は既に受検済みです。');
        } else {
          setError('質問の取得に失敗しました');
        }
      } finally {
        setLoading(false);
      }
    };

    loadQuestions();
    return () => {
      if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    };
  }, []);

  const handleAnswerChange = (questionId: string, value: number) => {
    const validatedValue = Math.max(1, Math.min(4, value));
    const newAnswers = { ...answers, [questionId]: validatedValue };
    setAnswers(newAnswers);
    debouncedSave(newAnswers);
    if (error.includes('有効な回答')) setError('');
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await stressCheckApi.saveDraft(answers);
      setInfo('回答を保存しました');
      setTimeout(() => setInfo(''), 3000);
    } catch {
      setError('保存に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setInfo('');

    if (Object.keys(answers).length !== 57) {
      setError(`全ての質問に回答してください（現在: ${Object.keys(answers).length}/57）`);
      return;
    }

    for (const [qId, value] of Object.entries(answers)) {
      if (typeof value !== 'number' || value < 1 || value > 4) {
        setError('有効な回答を選択してください');
        return;
      }
    }

    setSubmitting(true);

    try {
      const result = await stressCheckApi.submit({ answers });
      setSuccess(true);
      setTimeout(() => {
        router.push(`/stress-check/result/${result.id}`);
      }, 1500);
    } catch (err: any) {
      if (!err.response) {
        setError('ネットワークエラーが発生しました');
      } else if (err.response?.status === 400 && err.response?.data?.detail?.includes('既に受検済み')) {
        setInfo('この期間は既に受検済みです。');
      } else {
        setError(err.response?.data?.detail || '送信に失敗しました');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const answerLabels = ['そうだ', 'まあそうだ', 'ややちがう', 'ちがう'];

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <IconLoader className="w-10 h-10 animate-spin text-primary-500 mx-auto mb-4" />
          <p className="text-sand-600">質問を読み込んでいます...</p>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="page-container flex items-center justify-center">
        <div className="card p-8 text-center animate-scale-in max-w-md">
          <div className="w-16 h-16 rounded-full bg-success-light flex items-center justify-center mx-auto mb-4">
            <IconCheckCircle className="w-8 h-8 text-success" />
          </div>
          <h2 className="text-xl font-bold text-sand-900 mb-2">回答完了</h2>
          <p className="text-sand-600">ストレスチェックの回答が送信されました</p>
          <p className="text-sm text-sand-500 mt-4">結果ページに移動しています...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <Header title="ストレスチェック" showHome />

      <main className="page-content">
        {/* Progress Header */}
        <div className="card p-6 mb-6 animate-fade-in">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
              <IconClipboard className="w-6 h-6 text-primary-600" />
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-bold text-sand-900">職業性ストレス簡易調査票</h1>
              <p className="text-sm text-sand-600">57項目 | 厚労省指針準拠</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-primary-600">{totalAnswered}/57</div>
              <div className="text-xs text-sand-500">回答済み</div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="progress h-3">
            <div
              className="progress-bar"
              style={{ width: `${(totalAnswered / 57) * 100}%` }}
            />
          </div>

          {/* Section Tabs */}
          <div className="flex gap-2 mt-4">
            {sections.map((section, idx) => {
              const sectionAnswered = questions.slice(section.start, section.end)
                .filter(q => answers[q.id] !== undefined).length;
              const sectionTotal = section.end - section.start;
              const isComplete = sectionAnswered === sectionTotal;

              return (
                <button
                  key={idx}
                  onClick={() => setCurrentSection(idx)}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    currentSection === idx
                      ? 'bg-primary-500 text-white shadow-glow'
                      : isComplete
                        ? 'bg-success-light text-success-dark'
                        : 'bg-sand-100 text-sand-600 hover:bg-sand-200'
                  }`}
                >
                  <span className="block truncate">{section.title}</span>
                  <span className="text-xs opacity-80">{sectionAnswered}/{sectionTotal}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="alert-danger mb-6 animate-fade-in-down">{error}</div>
        )}
        {info && (
          <div className="alert-info mb-6 animate-fade-in-down">{info}</div>
        )}

        {/* Questions */}
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 mb-6">
            {sectionQuestions.map((question, idx) => (
              <div
                key={question.id}
                className={`card p-5 animate-fade-in-up ${
                  answers[question.id] !== undefined ? 'ring-2 ring-primary-200' : ''
                }`}
                style={{ animationDelay: `${idx * 30}ms` }}
              >
                <div className="flex items-start gap-4 mb-4">
                  <span className="flex-shrink-0 w-8 h-8 rounded-full bg-sand-100 flex items-center justify-center text-sm font-medium text-sand-600">
                    {currentSectionData.start + idx + 1}
                  </span>
                  <p className="text-sand-800 pt-1">{question.text}</p>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pl-12">
                  {[1, 2, 3, 4].map((value) => (
                    <label
                      key={value}
                      className={`radio-card justify-center text-center py-3 ${
                        answers[question.id] === value
                          ? 'border-primary-500 bg-primary-50'
                          : ''
                      }`}
                    >
                      <input
                        type="radio"
                        name={question.id}
                        value={value}
                        checked={answers[question.id] === value}
                        onChange={() => handleAnswerChange(question.id, value)}
                      />
                      <span className={`text-sm font-medium ${
                        answers[question.id] === value ? 'text-primary-700' : 'text-sand-700'
                      }`}>
                        {answerLabels[value - 1]}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Navigation */}
          <div className="card p-4 flex items-center justify-between gap-4">
            <button
              type="button"
              onClick={() => setCurrentSection(Math.max(0, currentSection - 1))}
              disabled={currentSection === 0}
              className="btn-secondary"
            >
              <IconChevronLeft className="w-4 h-4" />
              <span>前へ</span>
            </button>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="btn-secondary"
              >
                {saving ? <IconLoader className="w-4 h-4 animate-spin" /> : null}
                <span>{saving ? '保存中...' : '一時保存'}</span>
              </button>

              {currentSection === sections.length - 1 ? (
                <button
                  type="submit"
                  disabled={submitting || totalAnswered !== 57}
                  className="btn-primary"
                >
                  {submitting ? <IconLoader className="w-4 h-4 animate-spin" /> : null}
                  <span>{submitting ? '送信中...' : '回答を送信'}</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setCurrentSection(Math.min(sections.length - 1, currentSection + 1))}
                  className="btn-primary"
                >
                  <span>次へ</span>
                  <IconChevronRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </form>
      </main>
    </div>
  );
}
