'use client';

import { DepartmentStat } from '@/lib/api/dashboard';

interface DepartmentHeatmapProps {
  departments: DepartmentStat[];
}

/**
 * 部署ごとのストレスレベルをヒートマップ形式で可視化するコンポーネント
 * ストレススコアに応じて色が変わり、高ストレス部署を視覚的に識別できる
 */
export function DepartmentHeatmap({ departments }: DepartmentHeatmapProps) {
  if (departments.length === 0) {
    return (
      <div className="text-center py-8 text-sand-500">
        部署データがありません
      </div>
    );
  }

  // スコアの最大値と最小値を取得（正規化用）
  const scores = departments.map((d) => d.average_score);
  const maxScore = Math.max(...scores, 100);
  const minScore = Math.min(...scores, 0);

  /**
   * ストレススコアに基づいて色を決定
   * - 低ストレス（0-40）: 緑系
   * - 中ストレス（40-70）: 黄色〜オレンジ系
   * - 高ストレス（70+）: 赤系
   */
  const getHeatmapColor = (score: number): string => {
    if (score >= 70) {
      // 高ストレス: 赤系のグラデーション
      const intensity = Math.min((score - 70) / 30, 1);
      return `rgba(239, 68, 68, ${0.6 + intensity * 0.4})`; // danger色
    } else if (score >= 50) {
      // 中〜高ストレス: オレンジ系
      const intensity = (score - 50) / 20;
      return `rgba(245, 158, 11, ${0.5 + intensity * 0.4})`; // accent/warning色
    } else if (score >= 30) {
      // 低〜中ストレス: 黄色系
      const intensity = (score - 30) / 20;
      return `rgba(250, 204, 21, ${0.4 + intensity * 0.3})`; // yellow
    } else {
      // 低ストレス: 緑系
      const intensity = score / 30;
      return `rgba(16, 185, 129, ${0.4 + intensity * 0.3})`; // success色
    }
  };

  /**
   * スコアに応じたテキストカラーを取得
   */
  const getTextColor = (score: number): string => {
    if (score >= 70) return 'text-white';
    if (score >= 50) return 'text-sand-900';
    return 'text-sand-800';
  };

  /**
   * リスクレベルのラベルを取得
   */
  const getRiskLabel = (score: number): { text: string; className: string } => {
    if (score >= 70) return { text: '要注意', className: 'bg-white/90 text-danger' };
    if (score >= 50) return { text: '注意', className: 'bg-white/80 text-accent-600' };
    return { text: '良好', className: 'bg-white/70 text-success' };
  };

  // 部署をスコア順（高い順）にソート
  const sortedDepartments = [...departments].sort(
    (a, b) => b.average_score - a.average_score
  );

  return (
    <div className="space-y-4">
      {/* 凡例 */}
      <div className="flex items-center justify-between text-xs text-sand-600">
        <div className="flex items-center gap-4">
          <span className="font-medium">ストレスレベル:</span>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <div className="w-4 h-4 rounded bg-success/60"></div>
              <span>低</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-4 h-4 rounded bg-yellow-400/60"></div>
              <span>中</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-4 h-4 rounded bg-accent-500/70"></div>
              <span>やや高</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-4 h-4 rounded bg-danger/80"></div>
              <span>高</span>
            </div>
          </div>
        </div>
      </div>

      {/* ヒートマップグリッド */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {sortedDepartments.map((dept, idx) => {
          const bgColor = getHeatmapColor(dept.average_score);
          const textColor = getTextColor(dept.average_score);
          const riskLabel = getRiskLabel(dept.average_score);

          return (
            <div
              key={dept.department_name}
              className="relative p-4 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-lg cursor-pointer animate-fade-in-up group"
              style={{
                backgroundColor: bgColor,
                animationDelay: `${idx * 50}ms`,
              }}
            >
              {/* 部署名 */}
              <div className={`font-medium text-sm mb-2 truncate ${textColor}`}>
                {dept.department_name}
              </div>

              {/* スコア */}
              <div className={`text-2xl font-bold ${textColor}`}>
                {dept.average_score.toFixed(1)}
              </div>

              {/* 詳細情報 */}
              <div className={`text-xs mt-2 ${textColor} opacity-80`}>
                <div>従業員: {dept.employee_count}名</div>
                {dept.high_stress_count > 0 && (
                  <div className="mt-1">
                    高ストレス: {dept.high_stress_count}名
                  </div>
                )}
              </div>

              {/* リスクラベル */}
              <div
                className={`absolute top-2 right-2 px-2 py-0.5 rounded-full text-xs font-medium ${riskLabel.className}`}
              >
                {riskLabel.text}
              </div>

              {/* ホバー時の詳細ツールチップ */}
              <div className="absolute inset-0 bg-sand-900/90 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-4 flex flex-col justify-center text-white">
                <div className="text-sm font-medium mb-2">{dept.department_name}</div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span>平均スコア:</span>
                    <span className="font-medium">{dept.average_score.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>従業員数:</span>
                    <span className="font-medium">{dept.employee_count}名</span>
                  </div>
                  <div className="flex justify-between">
                    <span>高ストレス者:</span>
                    <span className={`font-medium ${dept.high_stress_count > 0 ? 'text-danger-light' : 'text-success-light'}`}>
                      {dept.high_stress_count}名
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>高ストレス率:</span>
                    <span className="font-medium">
                      {dept.employee_count > 0
                        ? ((dept.high_stress_count / dept.employee_count) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 統計サマリー */}
      <div className="mt-4 p-4 bg-sand-50 rounded-xl">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-lg font-bold text-danger">
              {sortedDepartments.filter((d) => d.average_score >= 70).length}
            </div>
            <div className="text-xs text-sand-600">要注意部署</div>
          </div>
          <div>
            <div className="text-lg font-bold text-accent-500">
              {sortedDepartments.filter((d) => d.average_score >= 50 && d.average_score < 70).length}
            </div>
            <div className="text-xs text-sand-600">注意部署</div>
          </div>
          <div>
            <div className="text-lg font-bold text-success">
              {sortedDepartments.filter((d) => d.average_score < 50).length}
            </div>
            <div className="text-xs text-sand-600">良好部署</div>
          </div>
        </div>
      </div>
    </div>
  );
}
