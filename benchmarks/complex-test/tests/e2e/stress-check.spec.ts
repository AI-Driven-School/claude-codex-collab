import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

test.describe('ストレスチェック機能', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'employee@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
  });

  test.describe('正常系', () => {
    test('57項目の質問が表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/stress-check`);

      // 質問が57項目表示されることを確認
      const questions = page.locator('.question-item');
      await expect(questions).toHaveCount(57);

      // 最初の質問が表示されることを確認
      await expect(questions.first()).toContainText('Q1');
    });

    test('全ての質問に回答して送信できる', async ({ page }) => {
      await page.goto(`${BASE_URL}/stress-check`);

      // 全ての質問に3を選択（標準的な回答）
      for (let i = 1; i <= 57; i++) {
        await page.click(`input[name="q${i}"][value="3"]`);
      }

      // 送信ボタンをクリック
      await page.click('button:has-text("送信")');

      // 送信成功メッセージを確認
      await expect(page.locator('.success-message')).toContainText('ストレスチェックの回答を送信しました');

      // 結果画面に遷移
      await expect(page).toHaveURL(new RegExp(`${BASE_URL}/stress-check/result`));
    });

    test('ストレスチェック結果が表示される', async ({ page }) => {
      // まずストレスチェックを実施
      await page.goto(`${BASE_URL}/stress-check`);
      for (let i = 1; i <= 57; i++) {
        await page.click(`input[name="q${i}"][value="3"]`);
      }
      await page.click('button:has-text("送信")');

      // 結果画面で以下が表示されることを確認
      await expect(page.locator('.total-score')).toBeVisible();
      await expect(page.locator('.is-high-stress')).toBeVisible();
      await expect(page.locator('.stress-reaction-score')).toBeVisible();
      await expect(page.locator('.job-stress-score')).toBeVisible();
      await expect(page.locator('.support-score')).toBeVisible();
    });

    test('高ストレス者と判定された場合に適切なメッセージが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/stress-check`);

      // 高ストレスになる回答（全て4を選択）
      for (let i = 1; i <= 57; i++) {
        await page.click(`input[name="q${i}"][value="4"]`);
      }

      await page.click('button:has-text("送信")');

      // 高ストレス者メッセージを確認
      await expect(page.locator('.is-high-stress')).toContainText('高ストレス者');
      await expect(page.locator('.recommendation-message')).toContainText('産業医への相談');
    });

    test('過去のストレスチェック結果を閲覧できる', async ({ page }) => {
      await page.goto(`${BASE_URL}/stress-check/history`);

      // 過去の結果がリスト表示される
      const historyItems = page.locator('.history-item');
      await expect(historyItems.first()).toBeVisible();
      await expect(historyItems.first().locator('.period')).toBeVisible();
      await expect(historyItems.first().locator('.score')).toBeVisible();
    });

    test('回答を保存して後で続きから再開できる', async ({ page }) => {
      await page.goto(`${BASE_URL}/stress-check`);

      // 一部の質問に回答
      for (let i = 1; i <= 10; i++) {
        await page.click(`input[name="q${i}"][value="3"]`);
      }

      // 保存ボタンをクリック
      await page.click('button:has-text("保存")');

      // 確認メッセージ
      await expect(page.locator('.info-message')).toContainText('回答を保存しました');

      // ページをリロード
      await page.reload();

      // 回答が保持されていることを確認
      for (let i = 1; i <= 10; i++) {
        await expect(page.locator(`input[name="q${i}"][value="3"]`)).toBeChecked();
      }
    });
  });

  test.describe('異常系', () => {
    test('未回答の質問がある場合に送信できない', async ({ page }) => {
      await page.goto(`${BASE_URL}/stress-check`);

      // 一部の質問のみ回答
      for (let i = 1; i <= 10; i++) {
        await page.click(`input[name="q${i}"][value="3"]`);
      }

      // 送信ボタンをクリック
      await page.click('button:has-text("送信")');

      // エラーメッセージを確認
      await expect(page.locator('.error-message')).toContainText('全ての質問に回答してください');
    });

    test('同じ期間に重複受検できない', async ({ page }) => {
      // 一度ストレスチェックを実施
      await page.goto(`${BASE_URL}/stress-check`);
      for (let i = 1; i <= 57; i++) {
        await page.click(`input[name="q${i}"][value="3"]`);
      }
      await page.click('button:has-text("送信")');

      // 再度同じ期間のストレスチェックページにアクセス
      await page.goto(`${BASE_URL}/stress-check`);

      // エラーメッセージまたは既に受検済みメッセージを確認
      await expect(page.locator('.error-message, .info-message')).toContainText(/既に受検済み|受検できません/);
    });

    test('無効な回答値でエラーが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/stress-check`);

      // 無効な値を設定（JavaScriptで直接操作）
      await page.evaluate(() => {
        const input = document.querySelector('input[name="q1"]') as HTMLInputElement;
        if (input) {
          input.value = '5'; // 無効な値
        }
      });

      // 送信を試みる
      await page.click('button:has-text("送信")');

      // バリデーションエラーを確認
      await expect(page.locator('.error-message')).toContainText('有効な回答を選択してください');
    });

    test('ネットワークエラー時に適切なエラーメッセージが表示される', async ({ page }) => {
      // ネットワークをオフラインに設定
      await page.context().setOffline(true);

      await page.goto(`${BASE_URL}/stress-check`);
      for (let i = 1; i <= 57; i++) {
        await page.click(`input[name="q${i}"][value="3"]`);
      }
      await page.click('button:has-text("送信")');

      // エラーメッセージを確認
      await expect(page.locator('.error-message')).toContainText('ネットワークエラーが発生しました');

      // オンラインに戻す
      await page.context().setOffline(false);
    });

    test('セッション切れの場合にログイン画面にリダイレクトされる', async ({ page }) => {
      // Cookieを削除
      await page.context().clearCookies();

      await page.goto(`${BASE_URL}/stress-check`);

      // ログイン画面にリダイレクト
      await expect(page).toHaveURL(`${BASE_URL}/login`);
    });
  });

  test.describe('管理者機能', () => {
    test.beforeEach(async ({ page }) => {
      // 管理者でログイン
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[name="email"]', 'admin@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');
    });

    test('未受検者一覧が表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard/stress-check`);

      // 未受検者リストが表示される
      await expect(page.locator('.non-taken-list')).toBeVisible();
      await expect(page.locator('.non-taken-item')).toHaveCount(/.+/); // 1件以上
    });

    test('未受検者にリマインドメールを送信できる', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard/stress-check`);

      // リマインドボタンをクリック
      await page.click('button:has-text("リマインド送信")');

      // 成功メッセージを確認
      await expect(page.locator('.success-message')).toContainText('リマインドメールを送信しました');
    });

    test('集団分析レポートをダウンロードできる', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard/stress-check`);

      // PDFダウンロードボタンをクリック
      const downloadPromise = page.waitForEvent('download');
      await page.click('button:has-text("レポートダウンロード")');
      const download = await downloadPromise;

      // PDFファイルがダウンロードされることを確認
      expect(download.suggestedFilename()).toMatch(/stress_check_report.*\.pdf$/);
    });
  });
});
