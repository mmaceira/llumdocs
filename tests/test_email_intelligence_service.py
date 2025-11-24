from __future__ import annotations

from unittest.mock import patch

import pytest

from llumdocs.services.email_intelligence_service import (
    DEFAULT_EMAIL_ROUTING_LABELS,
    ClassificationResult,
    EmailIntelligenceError,
    EmailIntelligenceService,
    analyze_sentiment,
    classify_email,
    detect_phishing,
)


@patch("llumdocs.services.email_intelligence_service._get_zero_shot_pipeline")
def test_classify_email_returns_sorted_labels(mock_pipeline):
    def fake_pipeline(text, candidate_labels, multi_label, hypothesis_template, **kwargs):
        assert text == "Factura incorrecta"
        assert candidate_labels == ["support", "billing"]
        assert multi_label is True
        assert "message" in hypothesis_template
        return {"labels": ["billing", "support"], "scores": [0.91, 0.12]}

    mock_pipeline.return_value = fake_pipeline

    result = classify_email(
        "Factura incorrecta",
        candidate_labels=["support", "billing"],
    )

    assert result.labels == ["billing", "support"]
    assert result.scores == [0.91, 0.12]


def test_classify_email_requires_labels():
    with pytest.raises(EmailIntelligenceError):
        classify_email("hola", candidate_labels=[" ", ""])


@patch("llumdocs.services.email_intelligence_service._get_phishing_pipeline")
@patch("llumdocs.services.email_intelligence_service._get_phishing_label_map")
def test_detect_phishing_returns_best_label(mock_label_map, mock_pipeline):
    def fake_pipeline(text, top_k, **kwargs):
        assert top_k is None
        return [
            [
                {"label": "LABEL_0", "score": 0.1},  # legitimate_email
                {"label": "LABEL_1", "score": 0.8},  # phishing_url
                {"label": "LABEL_2", "score": 0.05},  # legitimate_url
                {"label": "LABEL_3", "score": 0.05},  # phishing_url_alt
            ]
        ]

    mock_pipeline.return_value = fake_pipeline
    mock_label_map.return_value = {
        "LABEL_0": "legitimate_email",
        "LABEL_1": "phishing_url",
        "LABEL_2": "legitimate_url",
        "LABEL_3": "phishing_url_alt",
    }

    result = detect_phishing("Urgent password reset")

    # Should aggregate: safe = 0.1 + 0.05 = 0.15, phishing = 0.8 + 0.05 = 0.85
    assert result.label == "phishing"
    assert result.score == pytest.approx(0.85)
    assert result.scores_by_label["safe"] == pytest.approx(0.15)
    assert result.scores_by_label["phishing"] == pytest.approx(0.85)
    # Check individual labels are preserved
    assert result.scores_by_label["legitimate_email"] == pytest.approx(0.1)
    assert result.scores_by_label["phishing_url"] == pytest.approx(0.8)
    assert result.scores_by_label["legitimate_url"] == pytest.approx(0.05)
    assert result.scores_by_label["phishing_url_alt"] == pytest.approx(0.05)


@patch("llumdocs.services.email_intelligence_service._get_phishing_label_map")
@patch("llumdocs.services.email_intelligence_service._get_phishing_pipeline")
def test_detect_phishing_maps_label_x_to_readable(mock_pipeline, mock_label_map):
    """Test that LABEL_X format gets mapped to human-readable labels and aggregated."""

    def fake_pipeline(text, top_k, **kwargs):
        assert top_k is None
        return [
            [
                {"label": "LABEL_0", "score": 0.7},  # legitimate_email
                {"label": "LABEL_1", "score": 0.1},  # phishing_url
                {"label": "LABEL_2", "score": 0.15},  # legitimate_url
                {"label": "LABEL_3", "score": 0.05},  # phishing_url_alt
            ]
        ]

    mock_pipeline.return_value = fake_pipeline
    mock_label_map.return_value = {
        "LABEL_0": "legitimate_email",
        "LABEL_1": "phishing_url",
        "LABEL_2": "legitimate_url",
        "LABEL_3": "phishing_url_alt",
    }

    result = detect_phishing("Normal email")

    # Should aggregate: safe = 0.7 + 0.15 = 0.85, phishing = 0.1 + 0.05 = 0.15
    assert result.label == "safe"
    assert result.score == pytest.approx(0.85)
    assert "safe" in result.scores_by_label
    assert "phishing" in result.scores_by_label
    # Check all individual labels are preserved
    assert "legitimate_email" in result.scores_by_label
    assert "phishing_url" in result.scores_by_label
    assert "legitimate_url" in result.scores_by_label
    assert "phishing_url_alt" in result.scores_by_label
    assert "LABEL_0" not in result.scores_by_label
    assert "LABEL_1" not in result.scores_by_label


@patch("llumdocs.services.email_intelligence_service._get_sentiment_pipeline")
def test_analyze_sentiment_parses_prediction(mock_pipeline):
    def fake_pipeline(text, **kwargs):
        return [
            [
                {"label": "positive", "score": 0.73},
                {"label": "neutral", "score": 0.20},
                {"label": "negative", "score": 0.07},
            ]
        ]

    mock_pipeline.return_value = fake_pipeline

    result = analyze_sentiment("Molt bon servei")

    assert result.label == "positive"
    assert result.score == pytest.approx(0.73)
    assert result.scores_by_label["positive"] == pytest.approx(0.73)
    assert result.scores_by_label["neutral"] == pytest.approx(0.20)
    assert result.scores_by_label["negative"] == pytest.approx(0.07)


@patch("llumdocs.services.email_intelligence_service._get_phishing_label_map")
@patch("llumdocs.services.email_intelligence_service._get_sentiment_pipeline")
@patch("llumdocs.services.email_intelligence_service._get_phishing_pipeline")
@patch("llumdocs.services.email_intelligence_service._get_zero_shot_pipeline")
def test_email_intelligence_service_runs_all_pipelines(
    mock_zero_shot,
    mock_phishing,
    mock_sentiment,
    mock_label_map,
):
    mock_zero_shot.return_value = lambda *args, **kwargs: {
        "labels": ["support"],
        "scores": [0.99],
    }
    mock_phishing.return_value = lambda *args, **kwargs: [
        [
            {"label": "LABEL_0", "score": 0.7},  # legitimate_email
            {"label": "LABEL_1", "score": 0.1},  # phishing_url
            {"label": "LABEL_2", "score": 0.15},  # legitimate_url
            {"label": "LABEL_3", "score": 0.05},  # phishing_url_alt
        ]
    ]
    mock_label_map.return_value = {
        "LABEL_0": "legitimate_email",
        "LABEL_1": "phishing_url",
        "LABEL_2": "legitimate_url",
        "LABEL_3": "phishing_url_alt",
    }
    mock_sentiment.return_value = lambda *args, **kwargs: [
        [
            {"label": "neutral", "score": 0.55},
            {"label": "positive", "score": 0.30},
            {"label": "negative", "score": 0.15},
        ]
    ]

    service = EmailIntelligenceService(["support"])
    insights = service.analyze_email("Ping")

    assert insights.classification.labels == ["support"]
    # safe = 0.7 + 0.15 = 0.85, phishing = 0.1 + 0.05 = 0.15
    assert insights.phishing.label == "safe"
    assert insights.sentiment.label == "neutral"


@patch("llumdocs.services.email_intelligence_service.classify_email")
def test_email_intelligence_service_passes_template(mock_classify):
    mock_classify.return_value = ClassificationResult(labels=[], scores=[])
    service = EmailIntelligenceService(["support"], hypothesis_template="Topic: {}")

    service.classify("Hola")

    mock_classify.assert_called_with(
        "Hola",
        ["support"],
        multi_label=True,
        hypothesis_template="Topic: {}",
    )


@patch("llumdocs.services.email_intelligence_service.classify_email")
def test_email_intelligence_service_uses_default_labels(mock_classify):
    mock_classify.return_value = ClassificationResult(labels=[], scores=[])

    service = EmailIntelligenceService()
    service.classify("Bon dia")

    mock_classify.assert_called_with(
        "Bon dia",
        list(DEFAULT_EMAIL_ROUTING_LABELS),
        multi_label=True,
        hypothesis_template=None,
    )
