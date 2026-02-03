import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

test.describe('ダッシュボード機能', () => {
  test.beforeEach(async ({ page }) => {
    // 管理者でログイン
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
  });

  test.describe('正常系', () => {
    test('ダッシュボードが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // ダッシュボードの主要要素を確認
      await expect(page.locator('h1')).toContainText('ダッシュボード');
      await expect(page.locator('.stats-summary')).toBeVisible();
      await expect(page.locator('.department-heatmap')).toBeVisible();
    });

    test('統計サマリーが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // 統計情報が表示される
      await expect(page.locator('.total-employees')).toBeVisible();
      await expect(page.locator('.high-stress-count')).toBeVisible();
      await expect(page.locator('.stress-check-completion-rate')).toBeVisible();
    });

    test('部署別ヒートマップが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // ヒートマップが表示される
      await expect(page.locator('.department-heatmap')).toBeVisible();
      await expect(page.locator('.department-item')).toHaveCount(/.+/); // 1件以上

      // 部署名とストレスレベルが表示される
      const firstDept = page.locator('.department-item').first();
      await expect(firstDept.locator('.department-name')).toBeVisible();
      await expect(firstDept.locator('.stress-level')).toBeVisible();
    });

    test('AI改善提案が表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // AI提案セクションが表示される
      await expect(page.locator('.ai-recommendations')).toBeVisible();
      await expect(page.locator('.recommendation-item')).toHaveCount(/.+/); // 1件以上

      // 提案内容が表示される
      const firstRec = page.locator('.recommendation-item').first();
      await expect(firstRec.locator('.recommendation-title')).toBeVisible();
      await expect(firstRec.locator('.recommendation-description')).toBeVisible();
    });

    test('高ストレスアラート一覧が表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // アラートセクションが表示される
      await expect(page.locator('.alerts-section')).toBeVisible();
      await expect(page.locator('.alert-item')).toHaveCount(/.+/); // 0件以上（アラートがない場合もある）

      // アラートがある場合、詳細が表示される
      const alertCount = await page.locator('.alert-item').count();
      if (alertCount > 0) {
        const firstAlert = page.locator('.alert-item').first();
        await expect(firstAlert.locator('.alert-department')).toBeVisible();
        await expect(firstAlert.locator('.alert-level')).toBeVisible();
      }
    });

    test('期間フィルターでデータを絞り込める', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // 期間選択ドロップダウンをクリック
      await page.click('.period-filter');
      await page.click('text=過去30日');

      // データが更新されることを確認（ローディング後に）
      await page.waitForTimeout(1000);
      await expect(page.locator('.stats-summary')).toBeVisible();
    });

    test('部署フィルターでデータを絞り込める', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // 部署選択ドロップダウンをクリック
      await page.click('.department-filter');
      await page.click('text=開発部');

      // データが更新されることを確認
      await page.waitForTimeout(1000);
      await expect(page.locator('.stats-summary')).toBeVisible();
    });

    test('CSVエクスポートができる', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // CSVエクスポートボタンをクリック
      const downloadPromise = page.waitForEvent('download');
      await page.click('button:has-text("CSVエクスポート")');
      const download = await downloadPromise;

      // CSVファイルがダウンロードされることを確認
      expect(download.suggestedFilename()).toMatch(/dashboard.*\.csv$/);
    });

    test('詳細レポートページに遷移できる', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // 詳細レポートボタンをクリック
      await page.click('a:has-text("詳細レポート")');

      // 詳細レポートページに遷移
      await expect(page).toHaveURL(new RegExp(`${BASE_URL}/dashboard/report`));
    });
  });

  test.describe('異常系', () => {
    test('従業員ロールではダッシュボードにアクセスできない', async ({ page }) => {
      // 従業員でログイン
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[name="email"]', 'employee@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      // ダッシュボードにアクセスを試みる
      await page.goto(`${BASE_URL}/dashboard`);

      // アクセス拒否またはホーム画面にリダイレクト
      await expect(page).not.toHaveURL(`${BASE_URL}/dashboard`);
      await expect(page.locator('.error-message, .access-denied')).toBeVisible();
    });

    test('データが存在しない場合に適切なメッセージが表示される', async ({ page }) => {
      // 新規企業でログイン（データなし）
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[name="email"]', 'newadmin@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      await page.goto(`${BASE_URL}/dashboard`);

      // データなしメッセージが表示される
      await expect(page.locator('.no-data-message')).toBeVisible();
      await expect(page.locator('.no-data-message')).toContainText(/データがありません|まだデータが登録されていません/);
    });

    test('ネットワークエラー時に適切なエラーメッセージが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // ネットワークをオフラインに設定
      await page.context().setOffline(true);

      // ページをリロード
      await page.reload();

      // エラーメッセージを確認
      await expect(page.locator('.error-message')).toContainText('データの取得に失敗しました');

      // オンラインに戻す
      await page.context().setOffline(false);
    });

    test('セッション切れの場合にログイン画面にリダイレクトされる', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // Cookieを削除
      await page.context().clearCookies();

      // ページをリロード
      await page.reload();

      // ログイン画面にリダイレクト
      await expect(page).toHaveURL(`${BASE_URL}/login`);
    });
  });

  test.describe('集計分析機能', () => {
    test('部署別の平均ストレススコアが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // 部署別統計が表示される
      await expect(page.locator('.department-stats')).toBeVisible();
      await expect(page.locator('.department-stat-item')).toHaveCount(/.+/); // 1件以上

      // 平均スコアが表示される
      const firstStat = page.locator('.department-stat-item').first();
      await expect(firstStat.locator('.average-score')).toBeVisible();
    });

    test('時系列グラフが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // 時系列グラフが表示される
      await expect(page.locator('.time-series-chart')).toBeVisible();
      await expect(page.locator('.chart-container')).toBeVisible();
    });

    test('ストレスチェック受検率が表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);

      // 受検率が表示される
      await expect(page.locator('.completion-rate')).toBeVisible();
      const rate = await page.locator('.completion-rate').textContent();
      expect(rate).toMatch(/\d+%/); // パーセンテージ形式
    });
  });
});
