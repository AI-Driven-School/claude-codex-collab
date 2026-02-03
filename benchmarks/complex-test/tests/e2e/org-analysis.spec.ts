import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

test.describe('組織分析AIダッシュボード', () => {
  test.beforeEach(async ({ page }) => {
    // 管理者としてログイン
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/home');
  });

  test('管理者は組織分析ダッシュボードにアクセスできる', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // ページタイトルが表示される
    await expect(page.locator('h1')).toContainText('組織分析AIダッシュボード');
  });

  test('組織スコアカードが表示される', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // スコアカードが表示される
    await expect(page.getByTestId('org-score-card')).toBeVisible();
    await expect(page.getByTestId('response-rate-card')).toBeVisible();
    await expect(page.getByTestId('risk-dept-card')).toBeVisible();
  });

  test('AIインサイトパネルが表示される', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // AIインサイトパネルが表示される
    const insightsPanel = page.getByTestId('ai-insights-panel');
    await expect(insightsPanel).toBeVisible();

    // サマリー、リスク要因、改善提案が含まれる
    await expect(insightsPanel.locator('text=リスク要因')).toBeVisible();
    await expect(insightsPanel.locator('text=改善提案')).toBeVisible();
  });

  test('部署別スコア一覧が表示される', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // 部署リストが表示される
    const deptList = page.getByTestId('department-list');
    await expect(deptList).toBeVisible();

    // 少なくとも1つの部署行が存在する
    await expect(deptList.locator('[data-testid^="department-row-"]').first()).toBeVisible();
  });

  test('トレンドグラフが表示される', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // トレンドチャートが表示される
    await expect(page.getByTestId('trend-chart')).toBeVisible();
  });

  test('PDFレポート出力ボタンが機能する', async ({ page }) => {
    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // PDFボタンが表示される
    const pdfButton = page.getByTestId('export-pdf-button');
    await expect(pdfButton).toBeVisible();
    await expect(pdfButton).toContainText('PDFレポート出力');
  });

  test('ローディング状態が正しく表示される', async ({ page }) => {
    // ネットワーク遅延をシミュレート
    await page.route('**/api/v1/admin/org-analysis', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });

    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // ローディング表示
    await expect(page.getByTestId('org-analysis-loading')).toBeVisible();
  });

  test('一般ユーザーはアクセスできない（403エラー）', async ({ page }) => {
    // 一般ユーザーとしてログイン
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/home');

    // 組織分析ページにアクセス
    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // エラーが表示される
    await expect(page.getByTestId('org-analysis-error')).toBeVisible();
  });
});

test.describe('組織分析AI - エッジケース', () => {
  test('データがない場合でもクラッシュしない', async ({ page }) => {
    // APIを空のレスポンスでモック
    await page.route('**/api/v1/admin/org-analysis', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          organization_score: 0,
          score_change: 0,
          total_employees: 0,
          response_rate: 0,
          departments: [],
          trends: [],
          ai_insights: {
            summary: 'データがありません',
            risk_factors: [],
            recommendations: []
          },
          generated_at: new Date().toISOString()
        })
      });
    });

    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/home');

    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // ページがクラッシュせずに表示される
    await expect(page.getByTestId('org-score-card')).toBeVisible();
  });

  test('API エラー時にエラーメッセージが表示される', async ({ page }) => {
    // APIを500エラーでモック
    await page.route('**/api/v1/admin/org-analysis', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'サーバーエラーが発生しました' })
      });
    });

    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/home');

    await page.goto(`${BASE_URL}/admin/org-analysis`);

    // エラーメッセージが表示される
    await expect(page.getByTestId('org-analysis-error')).toBeVisible();
  });
});
