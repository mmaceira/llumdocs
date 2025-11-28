"""Integration tests for email intelligence models.

These tests verify that the actual models work correctly and return expected formats.
They require the email intelligence dependencies to be installed.
"""

from __future__ import annotations

import pytest

try:
    from llumdocs.services.email_intelligence_service import (
        EmailIntelligenceService,
        analyze_sentiment,
        classify_email,
        detect_phishing,
    )
except ImportError:
    pytest.skip("Email intelligence not available", allow_module_level=True)


@pytest.mark.integration
def test_classify_email_returns_all_categories():
    """Test that routing classification returns all candidate labels."""
    result = classify_email(
        "I need help with my invoice",
        candidate_labels=["support", "billing", "sales", "HR", "IT incident"],
    )

    assert len(result.labels) > 0
    assert len(result.scores) > 0
    assert len(result.labels) == len(result.scores)
    # All scores should be between 0 and 1 (probabilities)
    assert all(0 <= score <= 1 for score in result.scores)
    # Scores should sum to approximately 1 (for multi-label=False) or can be > 1
    # (for multi-label=True). With multi_label=True, each label is independent,
    # so sum can exceed 1


@pytest.mark.integration
def test_analyze_sentiment_returns_all_three_scores():
    """Test that sentiment analysis returns all 3 sentiment classes."""
    result = analyze_sentiment("This is a great service! I'm very happy.")

    # Should have all 3 sentiment labels
    assert "positive" in result.scores_by_label
    assert "neutral" in result.scores_by_label
    assert "negative" in result.scores_by_label

    # All scores should be between 0 and 1
    assert all(0 <= score <= 1 for score in result.scores_by_label.values())

    # Scores should sum to approximately 1 (softmax probabilities)
    total = sum(result.scores_by_label.values())
    assert 0.95 <= total <= 1.05, f"Scores should sum to ~1, got {total}"

    # Top label should match the highest score
    assert result.label in result.scores_by_label
    assert result.score == result.scores_by_label[result.label]


@pytest.mark.integration
def test_detect_phishing_returns_all_scores():
    """Test that phishing detection returns all detection scores."""
    result = detect_phishing("This is a normal email about a meeting.")

    # Should have aggregated scores
    assert "safe" in result.scores_by_label
    assert "phishing" in result.scores_by_label

    # Should have individual label scores
    assert len(result.scores_by_label) >= 2

    # All scores should be between 0 and 1
    assert all(0 <= score <= 1 for score in result.scores_by_label.values())

    # Top label should be either "safe" or "phishing"
    assert result.label in ("safe", "phishing")
    assert result.score == result.scores_by_label[result.label]


@pytest.mark.integration
def test_email_intelligence_service_integration():
    """Test the full EmailIntelligenceService workflow."""
    service = EmailIntelligenceService()

    email_text = "Hello, I need help with my account billing. Thank you!"

    # Test individual methods
    routing = service.classify(email_text)
    assert len(routing.labels) > 0
    assert len(routing.scores) > 0

    phishing = service.phishing(email_text)
    assert phishing.label in ("safe", "phishing")
    assert len(phishing.scores_by_label) > 0

    sentiment = service.sentiment(email_text)
    assert sentiment.label in ("positive", "neutral", "negative")
    assert len(sentiment.scores_by_label) == 3  # Should have all 3 sentiment scores
    assert "positive" in sentiment.scores_by_label
    assert "neutral" in sentiment.scores_by_label
    assert "negative" in sentiment.scores_by_label

    # Test combined analysis
    insights = service.analyze_email(email_text)
    assert insights.classification == routing
    assert insights.phishing == phishing
    assert insights.sentiment == sentiment
