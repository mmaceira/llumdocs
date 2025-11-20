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
    def fake_pipeline(text, candidate_labels, multi_label, hypothesis_template):
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
def test_detect_phishing_returns_best_label(mock_pipeline):
    def fake_pipeline(text, return_all_scores):
        assert return_all_scores is True
        return [[{"label": "safe", "score": 0.2}, {"label": "phishing", "score": 0.8}]]

    mock_pipeline.return_value = fake_pipeline

    result = detect_phishing("Urgent password reset")

    assert result.label == "phishing"
    assert result.score == pytest.approx(0.8)
    assert result.scores_by_label["safe"] == pytest.approx(0.2)


@patch("llumdocs.services.email_intelligence_service._get_phishing_label_map")
@patch("llumdocs.services.email_intelligence_service._get_phishing_pipeline")
def test_detect_phishing_maps_label_x_to_readable(mock_pipeline, mock_label_map):
    """Test that LABEL_X format gets mapped to human-readable labels."""

    def fake_pipeline(text, return_all_scores):
        assert return_all_scores is True
        return [[{"label": "LABEL_0", "score": 0.2}, {"label": "LABEL_1", "score": 0.8}]]

    mock_pipeline.return_value = fake_pipeline
    mock_label_map.return_value = {"LABEL_0": "safe", "LABEL_1": "phishing"}

    result = detect_phishing("Urgent password reset")

    assert result.label == "phishing"
    assert result.score == pytest.approx(0.8)
    assert "safe" in result.scores_by_label
    assert "phishing" in result.scores_by_label
    assert "LABEL_0" not in result.scores_by_label
    assert "LABEL_1" not in result.scores_by_label


@patch("llumdocs.services.email_intelligence_service._get_sentiment_pipeline")
def test_analyze_sentiment_parses_prediction(mock_pipeline):
    def fake_pipeline(text):
        return [{"label": "positive", "score": 0.73}]

    mock_pipeline.return_value = fake_pipeline

    result = analyze_sentiment("Molt bon servei")

    assert result.label == "positive"
    assert result.score == pytest.approx(0.73)


@patch("llumdocs.services.email_intelligence_service._get_sentiment_pipeline")
@patch("llumdocs.services.email_intelligence_service._get_phishing_pipeline")
@patch("llumdocs.services.email_intelligence_service._get_zero_shot_pipeline")
def test_email_intelligence_service_runs_all_pipelines(
    mock_zero_shot,
    mock_phishing,
    mock_sentiment,
):
    mock_zero_shot.return_value = lambda *args, **kwargs: {
        "labels": ["support"],
        "scores": [0.99],
    }
    mock_phishing.return_value = lambda *args, **kwargs: [[{"label": "safe", "score": 0.7}]]
    mock_sentiment.return_value = lambda *args, **kwargs: [{"label": "neutral", "score": 0.55}]

    service = EmailIntelligenceService(["support"])
    insights = service.analyze_email("Ping")

    assert insights.classification.labels == ["support"]
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
