import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

test.describe('認証機能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
  });

  test.describe('正常系', () => {
    test('管理者ログインが成功する', async ({ page }) => {
      // ログインフォームに入力
      await page.fill('input[name="email"]', 'admin@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      // ダッシュボードにリダイレクトされることを確認
      await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
      await expect(page.locator('h1')).toContainText('ダッシュボード');
    });

    test('従業員ログインが成功する', async ({ page }) => {
      await page.fill('input[name="email"]', 'employee@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      // 従業員用ホーム画面にリダイレクト
      await expect(page).toHaveURL(`${BASE_URL}/home`);
    });

    test('企業・ユーザー登録が成功する', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);

      // 企業情報入力
      await page.fill('input[name="companyName"]', 'テスト株式会社');
      await page.selectOption('select[name="industry"]', 'IT');
      await page.selectOption('select[name="planType"]', 'basic');

      // 管理者情報入力
      await page.fill('input[name="email"]', 'newadmin@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.fill('input[name="passwordConfirm"]', 'password123');
      await page.click('button[type="submit"]');

      // 登録成功メッセージを確認
      await expect(page.locator('.success-message')).toContainText('登録が完了しました');
    });

    test('ログアウトが成功する', async ({ page }) => {
      // ログイン
      await page.fill('input[name="email"]', 'admin@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      // ログアウト
      await page.click('button:has-text("ログアウト")');

      // ログイン画面にリダイレクト
      await expect(page).toHaveURL(`${BASE_URL}/login`);
    });
  });

  test.describe('異常系', () => {
    test('存在しないメールアドレスでログインに失敗する', async ({ page }) => {
      await page.fill('input[name="email"]', 'nonexistent@example.com');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      await expect(page.locator('.error-message')).toContainText('メールアドレスまたはパスワードが正しくありません');
    });

    test('間違ったパスワードでログインに失敗する', async ({ page }) => {
      await page.fill('input[name="email"]', 'admin@example.com');
      await page.fill('input[name="password"]', 'wrongpassword');
      await page.click('button[type="submit"]');

      await expect(page.locator('.error-message')).toContainText('メールアドレスまたはパスワードが正しくありません');
    });

    test('空のメールアドレスでバリデーションエラーが表示される', async ({ page }) => {
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      await expect(page.locator('input[name="email"]:invalid')).toBeVisible();
    });

    test('空のパスワードでバリデーションエラーが表示される', async ({ page }) => {
      await page.fill('input[name="email"]', 'admin@example.com');
      await page.click('button[type="submit"]');

      await expect(page.locator('input[name="password"]:invalid')).toBeVisible();
    });

    test('無効なメールアドレス形式でバリデーションエラーが表示される', async ({ page }) => {
      await page.fill('input[name="email"]', 'invalid-email');
      await page.fill('input[name="password"]', 'password123');
      await page.click('button[type="submit"]');

      await expect(page.locator('.error-message')).toContainText('有効なメールアドレスを入力してください');
    });

    test('パスワードが短すぎる場合にバリデーションエラーが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);
      await page.fill('input[name="password"]', 'short');
      await page.fill('input[name="passwordConfirm"]', 'short');

      await expect(page.locator('.error-message')).toContainText('パスワードは8文字以上で入力してください');
    });

    test('パスワード確認が一致しない場合にエラーが表示される', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);
      await page.fill('input[name="password"]', 'password123');
      await page.fill('input[name="passwordConfirm"]', 'password456');
      await page.click('button[type="submit"]');

      await expect(page.locator('.error-message')).toContainText('パスワードが一致しません');
    });

    test('既に登録済みのメールアドレスで登録に失敗する', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);
      await page.fill('input[name="companyName"]', 'テスト株式会社');
      await page.fill('input[name="email"]', 'admin@example.com'); // 既存のメール
      await page.fill('input[name="password"]', 'password123');
      await page.fill('input[name="passwordConfirm"]', 'password123');
      await page.click('button[type="submit"]');

      await expect(page.locator('.error-message')).toContainText('このメールアドレスは既に登録されています');
    });

    test('トークンが無効な場合にアクセスが拒否される', async ({ page }) => {
      // 無効なトークンを設定（Cookie）
      await page.context().addCookies([{
        name: 'access_token',
        value: 'invalid-token',
        url: BASE_URL,
      }]);

      await page.goto(`${BASE_URL}/dashboard`);

      // ログイン画面にリダイレクト
      await expect(page).toHaveURL(`${BASE_URL}/login`);
    });

    test('トークンが期限切れの場合にアクセスが拒否される', async ({ page }) => {
      // 期限切れトークンを設定（モック）
      await page.context().addCookies([{
        name: 'access_token',
        value: 'expired-token',
        url: BASE_URL,
      }]);

      await page.goto(`${BASE_URL}/dashboard`);

      // ログイン画面にリダイレクト
      await expect(page).toHaveURL(`${BASE_URL}/login`);
    });
  });
});
