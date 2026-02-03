import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

test.describe('CSV一括登録（ファイル未選択）', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.goto(`${BASE_URL}/admin/csv-import`);
  });

  test('ファイル未選択時は案内が表示され、プレビュー操作ができない', async ({ page }) => {
    await expect(page.getByTestId('csv-file-empty')).toBeVisible();
    await expect(page.getByTestId('csv-preview-button')).toHaveCount(0);
    await expect(page.getByTestId('csv-reset-button')).toHaveCount(0);
    await expect(page.getByTestId('csv-import-error')).toHaveCount(0);
  });

  test('CSV以外のファイルを選択するとエラーが表示される', async ({ page }) => {
    await page.getByTestId('csv-file-input').setInputFiles({
      name: 'invalid.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('not csv'),
    });

    await expect(page.getByTestId('csv-import-error')).toContainText('CSVファイルのみアップロード可能です');
    await expect(page.getByTestId('csv-file-empty')).toBeVisible();
    await expect(page.getByTestId('csv-preview-button')).toHaveCount(0);
  });
});
