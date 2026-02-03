"""
AIサービスのテスト（モック使用）
"""
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from app.services.ai_service import (
    contains_inappropriate_content,
    analyze_sentiment,
    generate_improvement_recommendations,
    _generate_fallback_recommendations
)


class TestContainsInappropriateContent:
    """不適切コンテンツ検出のテスト"""

    def test_normal_text(self):
        """通常のテキスト"""
        assert contains_inappropriate_content("今日も仕事頑張りました") is False
        assert contains_inappropriate_content("少し疲れています") is False

    def test_inappropriate_text(self):
        """不適切なテキスト"""
        assert contains_inappropriate_content("暴力的な表現") is True
        assert contains_inappropriate_content("自殺したい") is True

    def test_empty_text(self):
        """空のテキスト"""
        assert contains_inappropriate_content("") is False


class TestAnalyzeSentiment:
    """感情分析のテスト"""

    @pytest.mark.asyncio
    async def test_inappropriate_content_returns_default(self):
        """不適切なコンテンツはデフォルト値を返す"""
        result = await analyze_sentiment("暴力的な内容")

        assert result["sentiment"] == -0.5
        assert result["urgency"] == 3
        assert "inappropriate_content" in result["risk_flags"]

    @pytest.mark.asyncio
    @patch("app.services.ai_service.client")
    async def test_api_success(self, mock_client):
        """API呼び出し成功時"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "sentiment": 0.5,
                "topics": ["業務量"],
                "urgency": 2,
                "reply_suggestion": "お疲れ様です",
                "risk_flags": []
            })))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = await analyze_sentiment("今日は忙しかったです")

        assert result["sentiment"] == 0.5
        assert "業務量" in result["topics"]
        assert result["urgency"] == 2

    @pytest.mark.asyncio
    @patch("app.services.ai_service.client")
    async def test_api_error_returns_default(self, mock_client):
        """APIエラー時はデフォルト値を返す"""
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        result = await analyze_sentiment("テストメッセージ")

        assert result["sentiment"] == 0.0
        assert result["urgency"] == 1
        assert result["topics"] == []


class TestGenerateFallbackRecommendations:
    """フォールバック提案生成のテスト"""

    def test_high_stress_recommendation(self):
        """高ストレス者が多い場合の提案"""
        overall_stats = {
            "total_employees": 100,
            "high_stress_count": 30,
            "stress_check_completion_rate": 90
        }
        department_stats = []

        result = _generate_fallback_recommendations(department_stats, overall_stats)

        assert len(result) > 0
        assert any("高ストレス者" in r["title"] for r in result)

    def test_low_completion_rate_recommendation(self):
        """受検率が低い場合の提案"""
        overall_stats = {
            "total_employees": 100,
            "high_stress_count": 5,
            "stress_check_completion_rate": 50
        }
        department_stats = []

        result = _generate_fallback_recommendations(department_stats, overall_stats)

        assert any("受検" in r["title"] for r in result)

    def test_department_high_stress_recommendation(self):
        """部署別高ストレスの提案"""
        overall_stats = {
            "total_employees": 100,
            "high_stress_count": 10,
            "stress_check_completion_rate": 90
        }
        department_stats = [
            {
                "department_name": "開発部",
                "high_stress_count": 5,
                "employee_count": 10
            }
        ]

        result = _generate_fallback_recommendations(department_stats, overall_stats)

        assert any("開発部" in r.get("department_name", "") for r in result)

    def test_max_four_recommendations(self):
        """最大4件まで"""
        overall_stats = {
            "total_employees": 100,
            "high_stress_count": 50,
            "stress_check_completion_rate": 30
        }
        department_stats = [
            {"department_name": f"部署{i}", "high_stress_count": 5, "employee_count": 10}
            for i in range(10)
        ]

        result = _generate_fallback_recommendations(department_stats, overall_stats)

        assert len(result) <= 4


class TestGenerateImprovementRecommendations:
    """改善提案生成のテスト"""

    @pytest.mark.asyncio
    async def test_empty_data_returns_empty(self):
        """データが空の場合は空のリストを返す"""
        result = await generate_improvement_recommendations([], {"total_employees": 0})
        assert result == []

    @pytest.mark.asyncio
    @patch("app.services.ai_service.client")
    async def test_api_success(self, mock_client):
        """API呼び出し成功時"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "recommendations": [
                    {
                        "title": "残業時間削減",
                        "description": "ノー残業デーを導入",
                        "priority": "high"
                    }
                ]
            })))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        overall_stats = {
            "total_employees": 100,
            "high_stress_count": 20,
            "average_stress_score": 3.5,
            "stress_check_completion_rate": 85
        }
        department_stats = [
            {
                "department_name": "営業部",
                "average_score": 3.8,
                "high_stress_count": 10,
                "employee_count": 30
            }
        ]

        result = await generate_improvement_recommendations(department_stats, overall_stats)

        assert len(result) == 1
        assert result[0]["title"] == "残業時間削減"
        assert "id" in result[0]

    @pytest.mark.asyncio
    @patch("app.services.ai_service.client")
    async def test_api_error_returns_fallback(self, mock_client):
        """APIエラー時はフォールバック提案を返す"""
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        overall_stats = {
            "total_employees": 100,
            "high_stress_count": 30,
            "average_stress_score": 3.5,
            "stress_check_completion_rate": 85
        }
        department_stats = []

        result = await generate_improvement_recommendations(department_stats, overall_stats)

        assert len(result) > 0
        assert any("fallback" in r["id"] for r in result)
