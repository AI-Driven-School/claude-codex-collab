import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

test.describe('チャット・AI分析機能', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'employee@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
  });

  test.describe('正常系', () => {
    test('チャット画面が表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      // チャット画面の要素を確認
      await expect(page.locator('.chat-container')).toBeVisible();
      await expect(page.locator('.chat-input')).toBeVisible();
      await expect(page.locator('button:has-text("送信")')).toBeVisible();
    });

    test('メッセージを送信してAIからの返信を受け取れる', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      // メッセージを入力
      await page.fill('.chat-input', '今日は少し疲れました');
      await page.click('button:has-text("送信")');

      // AIからの返信が表示されることを確認
      await expect(page.locator('.ai-message')).toBeVisible();
      await expect(page.locator('.ai-message')).toContainText(/お疲れ様|無理をしない|大丈夫/);
    });

    test('複数のメッセージを送受信できる', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      // 1つ目のメッセージ
      await page.fill('.chat-input', '調子はどうですか？');
      await page.click('button:has-text("送信")');
      await expect(page.locator('.user-message').first()).toContainText('調子はどうですか？');

      // 2つ目のメッセージ
      await page.fill('.chat-input', '最近残業が多くて大変です');
      await page.click('button:has-text("送信")');
      await expect(page.locator('.user-message').last()).toContainText('最近残業が多くて大変です');
    });

    test('感情スコアが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      await page.fill('.chat-input', '今日はとても良い気分です');
      await page.click('button:has-text("送信")');

      // 感情スコアが表示される（正の値）
      await expect(page.locator('.sentiment-score')).toBeVisible();
      const score = await page.locator('.sentiment-score').textContent();
      expect(parseFloat(score || '0')).toBeGreaterThan(0);
    });

    test('チャット履歴が保存され、過去の会話を閲覧できる', async ({ page }) => {
      // メッセージを送信
      await page.goto(`${BASE_URL}/chat`);
      await page.fill('.chat-input', 'テストメッセージ');
      await page.click('button:has-text("送信")');

      // ページをリロード
      await page.reload();

      // 過去のメッセージが表示される
      await expect(page.locator('.chat-history')).toBeVisible();
      await expect(page.locator('.user-message')).toContainText('テストメッセージ');
    });

    test('絵文字を含むメッセージを送信できる', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      await page.fill('.chat-input', '今日は😊良い気分です');
      await page.click('button:has-text("送信")');

      // メッセージが正しく表示される
      await expect(page.locator('.user-message')).toContainText('今日は😊良い気分です');
    });
  });

  test.describe('異常系', () => {
    test('空のメッセージを送信できない', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      // 送信ボタンをクリック（メッセージ未入力）
      await page.click('button:has-text("送信")');

      // エラーメッセージまたは送信されないことを確認
      const messageCount = await page.locator('.user-message').count();
      expect(messageCount).toBe(0);
    });

    test('1000文字を超えるメッセージを送信できない', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      // 1001文字のメッセージを作成
      const longMessage = 'あ'.repeat(1001);
      await page.fill('.chat-input', longMessage);

      // バリデーションエラーを確認
      await expect(page.locator('.error-message, .chat-input:invalid')).toBeVisible();
    });

    test('レート制限に達した場合にエラーメッセージが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      // 10回メッセージを送信（レート制限）
      for (let i = 0; i < 10; i++) {
        await page.fill('.chat-input', `メッセージ${i}`);
        await page.click('button:has-text("送信")');
        await page.waitForTimeout(100); // 少し待機
      }

      // 11回目の送信を試みる
      await page.fill('.chat-input', '11回目のメッセージ');
      await page.click('button:has-text("送信")');

      // レート制限エラーを確認
      await expect(page.locator('.error-message')).toContainText('送信回数の上限に達しました');
    });

    test('ネットワークエラー時に適切なエラーメッセージが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      // ネットワークをオフラインに設定
      await page.context().setOffline(true);

      await page.fill('.chat-input', 'テストメッセージ');
      await page.click('button:has-text("送信")');

      // エラーメッセージを確認
      await expect(page.locator('.error-message')).toContainText('ネットワークエラーが発生しました');

      // オンラインに戻す
      await page.context().setOffline(false);
    });

    test('不適切なコンテンツがフィルタリングされる', async ({ page }) => {
      await page.goto(`${BASE_URL}/chat`);

      // 不適切なメッセージを送信
      await page.fill('.chat-input', '暴力的な内容のメッセージ');
      await page.click('button:has-text("送信")');

      // フィルタリングメッセージを確認
      await expect(page.locator('.warning-message')).toContainText('不適切な内容が検出されました');
    });
  });

  test.describe('AI分析機能', () => {
    test('日次スコアがダッシュボードに表示される', async ({ page }) => {
      // 管理者でログイン
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[name="email"]', 'admin@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      await page.goto(`${BASE_URL}/dashboard`);

      // 日次スコアが表示される
      await expect(page.locator('.daily-scores')).toBeVisible();
      await expect(page.locator('.sentiment-chart')).toBeVisible();
    });

    test('高リスク検知時にアラートが表示される', async ({ page }) => {
      // 管理者でログイン
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[name="email"]', 'admin@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      await page.goto(`${BASE_URL}/dashboard`);

      // アラートが表示される（モックデータまたは実際の高リスクデータ）
      await expect(page.locator('.alert-item')).toBeVisible();
      await expect(page.locator('.alert-item')).toContainText(/高ストレス|リスク検知/);
    });

    test('部署単位の集計データが表示される', async ({ page }) => {
      // 管理者でログイン
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[name="email"]', 'admin@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      await page.goto(`${BASE_URL}/dashboard`);

      // 部署別のヒートマップが表示される
      await expect(page.locator('.department-heatmap')).toBeVisible();
      await expect(page.locator('.department-item')).toHaveCount(/.+/); // 1件以上
    });
  });
});
