"""
PII（個人特定情報）除去フィルター
"""
import re


def clean_pii(text: str) -> str:
    """
    PII（個人特定情報）を除去
    
    Args:
        text: クリーニング対象のテキスト
    
    Returns:
        PIIが除去されたテキスト
    """
    # メールアドレスを置換
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # 電話番号を置換（日本の形式）
    text = re.sub(r'\b0\d{1,4}-\d{1,4}-\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b0\d{9,10}\b', '[PHONE]', text)
    
    # 社員番号パターンを置換（EMP-12345形式など）
    text = re.sub(r'\b[A-Z]{2,}-\d{4,}\b', '[EMPLOYEE_ID]', text)
    
    # 個人名（カタカナ・漢字）の検出は難しいため、簡易的なパターンマッチング
    # 実際の実装では、より高度なNLP技術を使用することを推奨
    
    return text
