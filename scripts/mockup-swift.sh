#!/bin/bash
# SwiftUI モックアップ生成ヘルパースクリプト
#
# 使用方法:
#   ./scripts/mockup-swift.sh "ログイン画面" "iPhone 15 Pro"
#   ./scripts/mockup-swift.sh "ダッシュボード" "iPad Pro 11"
#
# 注意: macOS + Xcode が必要です

set -e

NAME="$1"
DEVICE="${2:-iPhone 15 Pro}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "$NAME" ]; then
    echo "📱 SwiftUI モックアップ生成"
    echo ""
    echo "使用方法: $0 \"画面名\" [device]"
    echo ""
    echo "デバイス:"
    echo "  iPhone SE        : 375x667"
    echo "  iPhone 15        : 393x852"
    echo "  iPhone 15 Pro    : 393x852 (デフォルト)"
    echo "  iPhone 15 Pro Max: 430x932"
    echo "  iPad Pro 11      : 834x1194"
    echo "  iPad Pro 12.9    : 1024x1366"
    exit 1
fi

# macOSチェック
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ このスクリプトはmacOSでのみ動作します"
    exit 1
fi

# Xcodeチェック
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcodeがインストールされていません"
    echo "   App StoreからXcodeをインストールしてください"
    exit 1
fi

# ファイル名生成
FILENAME=$(echo "$NAME" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SWIFT_FILE="$PROJECT_DIR/mockups/temp-${TIMESTAMP}.swift"
PNG_FILE="$PROJECT_DIR/mockups/${FILENAME}-ios-${TIMESTAMP}.png"

mkdir -p "$PROJECT_DIR/mockups"

echo "📱 SwiftUI モックアップ生成: $NAME ($DEVICE)"
echo ""

# stdinからSwiftUIコードを読み込む
if [ -t 0 ]; then
    echo "⚠️  SwiftUIコードを標準入力から読み込むか、ファイルを指定してください"
    echo ""
    echo "例:"
    echo "  cat LoginView.swift | $0 \"$NAME\" \"$DEVICE\""
    echo "  $0 \"$NAME\" \"$DEVICE\" < LoginView.swift"
    exit 1
fi

# stdinからSwiftUIコードを読み込んで一時ファイルに保存
cat > "$SWIFT_FILE"

# レンダリング実行
swift "$PROJECT_DIR/scripts/render-mockup-swift.swift" "$SWIFT_FILE" "$PNG_FILE" "$DEVICE"

# 一時ファイル削除
rm -f "$SWIFT_FILE"

echo ""
echo "📎 Markdownで使用:"
echo "![${NAME}](./mockups/$(basename "$PNG_FILE"))"
