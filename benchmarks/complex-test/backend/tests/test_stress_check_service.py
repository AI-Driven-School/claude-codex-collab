"""
ストレスチェックサービスのテスト
"""
import os
import pytest

os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from app.services.stress_check_service import calculate_stress_scores, is_high_stress


class TestCalculateStressScores:
    """スコア計算のテスト"""

    def test_calculate_with_all_answers(self):
        """全ての回答がある場合のスコア計算"""
        answers = {f"q{i}": 3 for i in range(1, 58)}
        scores = calculate_stress_scores(answers)

        assert "job_stress_score" in scores
        assert "stress_reaction_score" in scores
        assert "support_score" in scores
        assert "satisfaction_score" in scores
        assert "total_score" in scores

        # 全て3なら各スコアは3.0になるはず
        assert scores["job_stress_score"] == 3.0
        assert scores["support_score"] == 3.0
        assert scores["satisfaction_score"] == 3.0

    def test_calculate_with_partial_answers(self):
        """一部の回答のみの場合のスコア計算"""
        answers = {"q1": 4, "q2": 3, "q3": 2, "q4": 1}
        scores = calculate_stress_scores(answers)

        # job_quantity = (4 + 3 + 2 + 1) / 4 = 2.5
        # 他は0なのでjob_stress_scoreは 2.5 / 5 = 0.5
        assert scores["job_stress_score"] == 0.5
        assert scores["total_score"] == 10  # 4 + 3 + 2 + 1

    def test_calculate_with_empty_answers(self):
        """空の回答"""
        answers = {}
        scores = calculate_stress_scores(answers)

        assert scores["job_stress_score"] == 0.0
        assert scores["stress_reaction_score"] == 0.0
        assert scores["support_score"] == 0.0
        assert scores["total_score"] == 0

    def test_calculate_high_stress_scores(self):
        """高ストレス傾向のスコア計算"""
        # ストレス反応関連（q18-q46）を高くする
        answers = {}
        for i in range(18, 47):
            answers[f"q{i}"] = 4

        scores = calculate_stress_scores(answers)
        assert scores["stress_reaction_score"] > 3.0


class TestIsHighStress:
    """高ストレス判定のテスト"""

    def test_high_stress_reaction_is_high_stress(self):
        """ストレス反応が高い場合は高ストレス"""
        assert is_high_stress(
            stress_reaction_score=3.5,
            job_stress_score=2.0,
            support_score=3.0
        ) is True

    def test_medium_stress_with_high_job_stress_is_high_stress(self):
        """中程度のストレス反応 + 高い仕事ストレスは高ストレス"""
        assert is_high_stress(
            stress_reaction_score=2.5,
            job_stress_score=3.5,
            support_score=3.0
        ) is True

    def test_medium_stress_with_low_support_is_high_stress(self):
        """中程度のストレス反応 + 低いサポートは高ストレス"""
        assert is_high_stress(
            stress_reaction_score=2.5,
            job_stress_score=2.0,
            support_score=1.5
        ) is True

    def test_low_stress_is_not_high_stress(self):
        """低ストレスは高ストレスではない"""
        assert is_high_stress(
            stress_reaction_score=1.5,
            job_stress_score=2.0,
            support_score=3.0
        ) is False

    def test_borderline_stress_reaction(self):
        """境界値テスト: stress_reaction_score = 3.0"""
        assert is_high_stress(
            stress_reaction_score=3.0,
            job_stress_score=2.0,
            support_score=3.0
        ) is True

    def test_borderline_medium_stress(self):
        """境界値テスト: stress_reaction_score = 2.0"""
        assert is_high_stress(
            stress_reaction_score=2.0,
            job_stress_score=3.0,
            support_score=3.0
        ) is True

    def test_not_high_stress_when_support_at_boundary(self):
        """境界値テスト: support_score = 2.0は低サポートではない"""
        assert is_high_stress(
            stress_reaction_score=2.5,
            job_stress_score=2.0,
            support_score=2.0
        ) is False
