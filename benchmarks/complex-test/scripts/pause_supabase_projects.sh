#!/bin/bash
# Supabase プロジェクト一括Pauseスクリプト
# 使い方: ./pause_supabase_projects.sh

# Supabase Access Token (https://supabase.com/dashboard/account/tokens で取得)
# 環境変数から読み込むか、直接設定
SUPABASE_ACCESS_TOKEN="${SUPABASE_ACCESS_TOKEN:-}"

if [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
  echo "エラー: SUPABASE_ACCESS_TOKEN が設定されていません"
  echo ""
  echo "以下の手順でトークンを取得してください:"
  echo "1. https://supabase.com/dashboard/account/tokens にアクセス"
  echo "2. 'Generate new token' をクリック"
  echo "3. トークンをコピー"
  echo ""
  echo "実行方法:"
  echo "  export SUPABASE_ACCESS_TOKEN='your-token-here'"
  echo "  ./pause_supabase_projects.sh"
  exit 1
fi

# Pauseするプロジェクトのリスト (Reference ID)
# ここに不要なプロジェクトを追加してください
PROJECTS_TO_PAUSE=(
  # 重複プロジェクト
  "wpzydnspjnpiyfrrvvop"  # NORTH STAR (NorthStar と重複)
  "wotbxwtrlfrgnlbaeevv"  # Rise_Predict (risehoops-predict と重複)
  "mifgebrpiykijjlqrjfr"  # FinRoute-DB (FinRouteDB と重複)
  "izfzrjesaoibihbmqesg"  # StressAIAgent (stress-ai-agent と重複)

  # 2024年の古いプロジェクト
  "unolahoyhoidetjbirge"  # yu010101's Project (2024-11)

  # 2025年前半の古いプロジェクト (必要に応じてコメントアウト解除)
  # "mzhnxvkzxfuzdfpcndec"  # basho
  # "afwpkddocmatgyjufwgo"  # NoteAI
  # "beyjlffwetpnijtwyzeb"  # pos-regi-plus
  # "csgqjeejjuugbkvaeahb"  # trend_music_search
  # "mglgwatdnccqvoorrgqo"  # STORE_SEO_TOOL
  # "soayonclzrrhqyfvjkwq"  # e-bok-dev
  # "fmonerzmxohwkisdagvm"  # AI_Reply
  # "sohkshgoqumgvziaoqwu"  # AI_Pub
  # "eqvujztifkwirsrckxfd"  # EEAT_Booster
  # "fshhrriipsndwnxjzeux"  # ChatReserve
  # "ryzmjiyqljeynzqqptjj"  # SalesGo
  # "kryicaaxjixqgxaaicxm"  # ShiftAI
)

echo "=== Supabase プロジェクト Pause スクリプト ==="
echo ""
echo "Pauseするプロジェクト数: ${#PROJECTS_TO_PAUSE[@]}"
echo ""

for ref in "${PROJECTS_TO_PAUSE[@]}"; do
  echo "Pausing: $ref ..."

  response=$(curl -s -X POST \
    "https://api.supabase.com/v1/projects/${ref}/pause" \
    -H "Authorization: Bearer ${SUPABASE_ACCESS_TOKEN}" \
    -H "Content-Type: application/json")

  if echo "$response" | grep -q "error"; then
    echo "  ❌ 失敗: $response"
  else
    echo "  ✅ 成功"
  fi

  # Rate limit対策
  sleep 1
done

echo ""
echo "完了しました！"
echo "削減効果: 約 \$${#PROJECTS_TO_PAUSE[@]} x 5 = \$$(( ${#PROJECTS_TO_PAUSE[@]} * 5 ))/月"
