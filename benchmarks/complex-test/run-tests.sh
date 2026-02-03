#!/bin/bash

# テスト実行スクリプト

set -e

echo "=== StressAgent Pro テスト実行スクリプト ==="
echo ""

# 1. Dockerの確認
echo "1. Dockerの状態を確認中..."
if ! docker ps > /dev/null 2>&1; then
    echo "⚠️  Dockerが起動していません。Dockerを起動してください。"
    echo "   Docker Desktopを起動するか、以下のコマンドで確認してください:"
    echo "   docker ps"
    exit 1
fi
echo "✅ Dockerは起動しています"

# 2. データベースの起動
echo ""
echo "2. データベースを起動中..."
cd "$(dirname "$0")"
docker-compose up -d
sleep 5
echo "✅ データベースが起動しました"

# 3. バックエンドの依存関係確認
echo ""
echo "3. バックエンドの依存関係を確認中..."
if [ ! -d "backend/venv" ]; then
    echo "⚠️  バックエンドの仮想環境が見つかりません。"
    echo "   以下のコマンドでセットアップしてください:"
    echo "   cd backend"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi
echo "✅ バックエンドの依存関係は準備済みです"

# 4. フロントエンドの依存関係確認
echo ""
echo "4. フロントエンドの依存関係を確認中..."
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  フロントエンドの依存関係が見つかりません。"
    echo "   以下のコマンドでインストールしてください:"
    echo "   cd frontend"
    echo "   npm install"
    exit 1
fi
echo "✅ フロントエンドの依存関係は準備済みです"

# 5. テスト実行
echo ""
echo "5. Playwrightテストを実行中..."
echo "   注意: バックエンドとフロントエンドのサーバーが自動的に起動します"
echo ""

npx playwright test

echo ""
echo "=== テスト実行完了 ==="
