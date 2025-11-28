"""
Email intelligence utilities powered by multilingual Hugging Face models.

The module bundles three complementary capabilities for enterprise email
and ticket workflows:

* Custom zero-shot classification for routing (department, topic, urgency)
* Dedicated phishing / spam detection
* Multilingual sentiment analysis (ca/es/en and 100+ languages)
"""

from __future__ import annotations

import gc
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

try:
    import torch
except Exception:  # pragma: no cover
    torch = None  # type: ignore[assignment]

from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Pipeline,
    pipeline,
)

ZERO_SHOT_MODEL_ID = os.getenv("LLUMDOCS_EMAIL_ZEROSHOT_MODEL", "MoritzLaurer/bge-m3-zeroshot-v2.0")
PHISHING_MODEL_ID = os.getenv(
    "LLUMDOCS_EMAIL_PHISHING_MODEL", "cybersectony/phishing-email-detection-distilbert_v2.1"
)
SENTIMENT_MODEL_ID = os.getenv(
    "LLUMDOCS_EMAIL_SENTIMENT_MODEL",
    "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
)
# Hugging Face email models typically cap their context at 512 tokens. Truncate inputs
# to avoid the RuntimeError seen when longer emails are analyzed.
MAX_EMAIL_SEQUENCE_LENGTH = int(os.getenv("LLUMDOCS_EMAIL_MAX_TOKENS", "512"))

# Default routing categories for email classification.
# The zero-shot model can classify into ANY labels you provide;
# these are sensible defaults for common enterprise email routing.
# You can override them by passing custom candidate_labels to EmailIntelligenceService.
DEFAULT_EMAIL_ROUTING_LABELS: Sequence[str] = [
    "support",
    "billing",
    "sales",
    "HR",
    "IT incident",
]


class EmailIntelligenceError(RuntimeError):
    """Raised when the email intelligence pipeline cannot run."""


def _check_email_intelligence_enabled() -> None:
    """Check if email intelligence is enabled via environment variable."""
    enabled = os.getenv("LLUMDOCS_ENABLE_EMAIL_INTELLIGENCE", "1")
    if enabled.lower() not in ("1", "true", "yes"):
        raise EmailIntelligenceError(
            "Email intelligence is disabled via LLUMDOCS_ENABLE_EMAIL_INTELLIGENCE. "
            "Set it to '1', 'true', or 'yes' to enable."
        )


@dataclass(frozen=True)
class ClassificationResult:
    labels: Sequence[str]
    scores: Sequence[float]


@dataclass(frozen=True)
class PhishingDetection:
    label: str
    score: float
    scores_by_label: Dict[str, float]


@dataclass(frozen=True)
class SentimentPrediction:
    label: str
    score: float
    scores_by_label: Dict[str, float]


@dataclass(frozen=True)
class EmailInsights:
    classification: ClassificationResult
    phishing: PhishingDetection
    sentiment: SentimentPrediction


# NOTE: pipelines are cached at module level and reused across requests.
# For high-throughput deployments, consider running email intelligence
# in a dedicated worker process or service.
_ZERO_SHOT_PIPELINE: Pipeline | None = None
_PHISHING_PIPELINE: Pipeline | None = None
_SENTIMENT_PIPELINE: Pipeline | None = None
_PHISHING_LABEL_MAP: Dict[str, str] | None = None


def _has_gpu_memory() -> bool:
    """
    Check if GPU is available and has free memory.

    Returns:
        True if GPU is available and has memory, False otherwise.
    """
    if torch is None:
        return False
    try:
        if not torch.cuda.is_available():  # type: ignore[attr-defined]
            return False
        # Check if there's at least 100MB free memory
        total_memory = torch.cuda.get_device_properties(0).total_memory  # type: ignore[attr-defined]
        allocated_memory = torch.cuda.memory_allocated(0)  # type: ignore[attr-defined]
        free_memory = total_memory - allocated_memory
        return free_memory > 100 * 1024 * 1024  # 100MB
    except Exception:  # noqa: BLE001
        return False


def _release_pipeline(global_name: str) -> None:
    """
    Release a cached Hugging Face pipeline and free GPU memory.

    Args:
        global_name: Name of the module-level variable storing the pipeline.
    """
    pipeline_obj = globals().get(global_name)
    if pipeline_obj is None:
        return

    globals()[global_name] = None

    model = getattr(pipeline_obj, "model", None)
    if model is not None and hasattr(model, "to"):
        try:
            model.to("cpu")
        except Exception:  # noqa: BLE001
            pass

    del pipeline_obj
    gc.collect()

    if torch is not None:
        try:
            if torch.cuda.is_available():  # type: ignore[attr-defined]
                torch.cuda.empty_cache()  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            pass


def _get_zero_shot_pipeline() -> Pipeline:
    global _ZERO_SHOT_PIPELINE
    if _ZERO_SHOT_PIPELINE is None:
        device = 0 if _has_gpu_memory() else -1  # 0 = GPU, -1 = CPU
        try:
            _ZERO_SHOT_PIPELINE = pipeline(
                "zero-shot-classification",
                model=ZERO_SHOT_MODEL_ID,
                device=device,
            )
        except (RuntimeError, OSError) as exc:
            # If GPU fails (out of memory or other error), try CPU
            if device == 0 and ("out of memory" in str(exc).lower() or "cuda" in str(exc).lower()):
                _ZERO_SHOT_PIPELINE = pipeline(
                    "zero-shot-classification",
                    model=ZERO_SHOT_MODEL_ID,
                    device=-1,  # Force CPU
                )
            else:
                raise
    return _ZERO_SHOT_PIPELINE


def _get_phishing_label_map() -> Dict[str, str]:
    """
    Get mapping from model's LABEL_X format to human-readable labels.

    The cybersectony/phishing-email-detection-distilbert_v2.1 model uses:
    - LABEL_0: legitimate_email (safe category)
    - LABEL_1: phishing_url (phishing category - note: label name is misleading,
      this class can match emails without URLs)
    - LABEL_2: legitimate_url (safe category)
    - LABEL_3: phishing_url_alt (phishing category - note: label name is misleading,
      this class can match emails without URLs)

    Note: The label names reference the training data structure but don't necessarily
    mean the model detected a URL. These are just class names.
    """
    global _PHISHING_LABEL_MAP
    if _PHISHING_LABEL_MAP is None:
        try:
            config = AutoConfig.from_pretrained(PHISHING_MODEL_ID)
            id2label = getattr(config, "id2label", {})
            if id2label:
                _PHISHING_LABEL_MAP = {}
                for label_id, label_name in id2label.items():
                    if label_name.startswith("LABEL_"):
                        # Map based on cybersectony model structure
                        # Keep original distinct label names to preserve all information
                        # Note: Label names reference training data categories but don't
                        # necessarily mean the model detected a URL in the input
                        if label_id == 0:
                            _PHISHING_LABEL_MAP[label_name] = "legitimate_email"
                        elif label_id == 1:
                            _PHISHING_LABEL_MAP[label_name] = "phishing_url"
                        elif label_id == 2:
                            _PHISHING_LABEL_MAP[label_name] = "legitimate_url"
                        elif label_id == 3:
                            _PHISHING_LABEL_MAP[label_name] = "phishing_url_alt"
                        else:
                            # For any additional labels beyond the known 4
                            _PHISHING_LABEL_MAP[label_name] = f"class_{label_id}"
                    else:
                        # Already readable - use as-is
                        _PHISHING_LABEL_MAP[label_name] = label_name
            else:
                # Fallback: create default mapping for the 4-class model
                _PHISHING_LABEL_MAP = {
                    "LABEL_0": "legitimate_email",
                    "LABEL_1": "phishing_url",
                    "LABEL_2": "legitimate_url",
                    "LABEL_3": "phishing_url_alt",
                }
        except Exception:  # noqa: BLE001
            # Fallback if config loading fails - use the known 4-class mapping
            _PHISHING_LABEL_MAP = {
                "LABEL_0": "legitimate_email",
                "LABEL_1": "phishing_url",
                "LABEL_2": "legitimate_url",
                "LABEL_3": "phishing_url_alt",
            }
    return _PHISHING_LABEL_MAP


def _get_phishing_pipeline() -> Pipeline:
    global _PHISHING_PIPELINE
    if _PHISHING_PIPELINE is None:
        device = 0 if _has_gpu_memory() else -1  # 0 = GPU, -1 = CPU
        try:
            _PHISHING_PIPELINE = pipeline(
                "text-classification",
                model=PHISHING_MODEL_ID,
                device=device,
            )
        except (RuntimeError, OSError) as exc:
            # If GPU fails (out of memory or other error), try CPU
            if device == 0 and ("out of memory" in str(exc).lower() or "cuda" in str(exc).lower()):
                _PHISHING_PIPELINE = pipeline(
                    "text-classification",
                    model=PHISHING_MODEL_ID,
                    device=-1,  # Force CPU
                )
            else:
                raise
    return _PHISHING_PIPELINE


def _get_sentiment_pipeline() -> Pipeline:
    global _SENTIMENT_PIPELINE
    if _SENTIMENT_PIPELINE is None:
        device = 0 if _has_gpu_memory() else -1  # 0 = GPU, -1 = CPU
        try:
            tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_ID)
            model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_ID)
            if device == 0:
                model = model.to("cuda")
            _SENTIMENT_PIPELINE = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=device,
            )
        except (RuntimeError, OSError) as exc:
            # If GPU fails (out of memory or other error), try CPU
            if device == 0 and ("out of memory" in str(exc).lower() or "cuda" in str(exc).lower()):
                tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_ID)
                model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_ID)
                _SENTIMENT_PIPELINE = pipeline(
                    "sentiment-analysis",
                    model=model,
                    tokenizer=tokenizer,
                    device=-1,  # Force CPU
                )
            else:
                raise
    return _SENTIMENT_PIPELINE


def _normalize_text(value: str, *, field_name: str = "text") -> str:
    normalized = value.strip()
    if not normalized:
        raise EmailIntelligenceError(f"{field_name} must not be empty.")
    return normalized


def _normalize_labels(candidate_labels: Iterable[str]) -> List[str]:
    normalized = [label.strip() for label in candidate_labels if label and label.strip()]
    if not normalized:
        raise EmailIntelligenceError("candidate_labels must include at least one non-empty label.")
    return list(dict.fromkeys(normalized))


def classify_email(
    text: str,
    candidate_labels: Iterable[str],
    *,
    multi_label: bool = True,
    hypothesis_template: str | None = None,
) -> ClassificationResult:
    """
    Classify an email/ticket into custom categories via zero-shot inference.
    """
    _check_email_intelligence_enabled()
    text_value = _normalize_text(text)
    labels = _normalize_labels(candidate_labels)
    template = hypothesis_template or "This message is about {}."

    pipeline_runner: Pipeline | None = None
    try:
        pipeline_runner = _get_zero_shot_pipeline()
        result = pipeline_runner(
            text_value,
            candidate_labels=labels,
            multi_label=multi_label,
            hypothesis_template=template,
            truncation=True,
            max_length=MAX_EMAIL_SEQUENCE_LENGTH,
        )
    except RuntimeError as exc:
        # If GPU out of memory during inference, try CPU fallback
        if "out of memory" in str(exc).lower() or "cuda" in str(exc).lower():
            _release_pipeline("_ZERO_SHOT_PIPELINE")
            # Force CPU pipeline creation
            global _ZERO_SHOT_PIPELINE
            _ZERO_SHOT_PIPELINE = pipeline(
                "zero-shot-classification",
                model=ZERO_SHOT_MODEL_ID,
                device=-1,  # Force CPU
            )
            pipeline_runner = _ZERO_SHOT_PIPELINE
            result = pipeline_runner(
                text_value,
                candidate_labels=labels,
                multi_label=multi_label,
                hypothesis_template=template,
                truncation=True,
                max_length=MAX_EMAIL_SEQUENCE_LENGTH,
            )
        else:
            raise EmailIntelligenceError(str(exc)) from exc
    except OSError as exc:  # Raised when a model cannot be loaded
        raise EmailIntelligenceError(str(exc)) from exc
    finally:
        if pipeline_runner is not None:
            _release_pipeline("_ZERO_SHOT_PIPELINE")

    return ClassificationResult(labels=list(result["labels"]), scores=list(result["scores"]))


def detect_phishing(text: str) -> PhishingDetection:
    """
    Detect whether an email is phishing/spam using a specialized classifier.

    Returns human-readable labels (e.g., "safe", "phishing") instead of
    model-internal labels (e.g., "LABEL_0", "LABEL_1").
    """
    _check_email_intelligence_enabled()
    text_value = _normalize_text(text)

    pipeline_runner: Pipeline | None = None
    try:
        pipeline_runner = _get_phishing_pipeline()
        raw = pipeline_runner(
            text_value,
            top_k=None,
            truncation=True,
            max_length=MAX_EMAIL_SEQUENCE_LENGTH,
        )
    except RuntimeError as exc:
        # If GPU out of memory during inference, try CPU fallback
        if "out of memory" in str(exc).lower() or "cuda" in str(exc).lower():
            _release_pipeline("_PHISHING_PIPELINE")
            # Force CPU pipeline creation
            global _PHISHING_PIPELINE
            _PHISHING_PIPELINE = pipeline(
                "text-classification",
                model=PHISHING_MODEL_ID,
                device=-1,  # Force CPU
            )
            pipeline_runner = _PHISHING_PIPELINE
            raw = pipeline_runner(
                text_value,
                top_k=None,
                truncation=True,
                max_length=MAX_EMAIL_SEQUENCE_LENGTH,
            )
        else:
            raise EmailIntelligenceError(str(exc)) from exc
    except OSError as exc:
        raise EmailIntelligenceError(str(exc)) from exc
    finally:
        if pipeline_runner is not None:
            _release_pipeline("_PHISHING_PIPELINE")

    # Pipeline returns list[ list[ {label, score} ] ]
    scores = raw[0] if raw and isinstance(raw[0], list) else raw
    if not isinstance(scores, list) or not scores:
        raise EmailIntelligenceError("Unexpected response from phishing model.")

    label_map = _get_phishing_label_map()

    # Map model labels to human-readable labels, keeping all individual scores
    ordered = {}
    for item in scores:
        if "label" in item and "score" in item:
            model_label = item["label"]
            readable_label = label_map.get(model_label, model_label)
            ordered[readable_label] = float(item["score"])

    if not ordered:
        raise EmailIntelligenceError("Phishing model returned no labels.")

    # Aggregate probabilities into safe vs phishing categories
    # Safe: legitimate_email + legitimate_url
    # Phishing: phishing_url + phishing_url_alt
    safe_score = ordered.get("legitimate_email", 0.0) + ordered.get("legitimate_url", 0.0)
    phishing_score = ordered.get("phishing_url", 0.0) + ordered.get("phishing_url_alt", 0.0)

    # Determine the best category (safe or phishing)
    if phishing_score > safe_score:
        best_label = "phishing"
        best_score = phishing_score
    else:
        best_label = "safe"
        best_score = safe_score

    # Include aggregated scores in the output for transparency
    aggregated = {
        "safe": safe_score,
        "phishing": phishing_score,
    }
    # Merge with individual label scores
    final_scores = {**ordered, **aggregated}

    return PhishingDetection(label=best_label, score=best_score, scores_by_label=final_scores)


def analyze_sentiment(text: str) -> SentimentPrediction:
    """
    Run multilingual sentiment analysis (positive/neutral/negative).
    """
    _check_email_intelligence_enabled()
    text_value = _normalize_text(text)

    pipeline_runner: Pipeline | None = None
    try:
        pipeline_runner = _get_sentiment_pipeline()
        # Use top_k=None to get all scores (replaces deprecated return_all_scores=True)
        # The sentiment-analysis pipeline with top_k=None should return all classes
        result = pipeline_runner(
            text_value,
            truncation=True,
            max_length=MAX_EMAIL_SEQUENCE_LENGTH,
            top_k=None,  # Get all scores for all sentiment classes
        )
    except RuntimeError as exc:
        # If GPU out of memory during inference, try CPU fallback
        if "out of memory" in str(exc).lower() or "cuda" in str(exc).lower():
            _release_pipeline("_SENTIMENT_PIPELINE")
            # Force CPU pipeline creation
            global _SENTIMENT_PIPELINE
            tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_ID)
            model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_ID)
            _SENTIMENT_PIPELINE = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=-1,  # Force CPU
            )
            pipeline_runner = _SENTIMENT_PIPELINE
            result = pipeline_runner(
                text_value,
                truncation=True,
                max_length=MAX_EMAIL_SEQUENCE_LENGTH,
                top_k=None,  # Get all scores for all sentiment classes
            )
        else:
            raise EmailIntelligenceError(str(exc)) from exc
    except OSError as exc:
        raise EmailIntelligenceError(str(exc)) from exc
    finally:
        if pipeline_runner is not None:
            _release_pipeline("_SENTIMENT_PIPELINE")

    # Handle different return formats: could be a list or list of lists
    # Pipeline returns list of results (one per input), so get first element
    if not isinstance(result, list) or len(result) == 0:
        raise EmailIntelligenceError(f"Pipeline returned invalid result: {type(result)}")

    predictions = result[0]

    # Handle different nested formats
    # With top_k=None, result format can vary:
    # - Sometimes: [[{...}, {...}, {...}]] (nested list)
    # - Sometimes: [{...}, {...}, {...}] (flat list)
    if isinstance(predictions, dict):
        # Single prediction dict - wrap in list (shouldn't happen with top_k=None)
        predictions = [predictions]
    elif isinstance(predictions, str):
        # String format - this shouldn't happen, but handle gracefully
        raise EmailIntelligenceError(
            f"Pipeline returned string instead of predictions. "
            f"Result format: {type(result)}, first element type: {type(predictions)}"
        )
    elif isinstance(predictions, list):
        # If predictions is a list of lists (nested), flatten it
        if predictions and isinstance(predictions[0], list):
            predictions = predictions[0]
    else:
        raise EmailIntelligenceError(
            f"Unexpected prediction format: {type(predictions)}. "
            f"Expected list or dict, got: {predictions}"
        )

    # Extract all scores and find the top prediction
    scores_by_label: Dict[str, float] = {}
    top_label = ""
    top_score = 0.0

    for pred in predictions:
        if not isinstance(pred, dict):
            continue
        label = str(pred.get("label", ""))
        score = float(pred.get("score", 0.0))
        # Always add the score, even if label is empty (shouldn't happen, but be safe)
        if label:
            scores_by_label[label] = score
            if score > top_score:
                top_score = score
                top_label = label
        # If label is empty but we have a score, still try to use it
        elif score > 0:
            # This shouldn't happen, but log it if it does
            scores_by_label[f"unknown_{len(scores_by_label)}"] = score

    # Ensure we have at least one score
    if not scores_by_label:
        raise EmailIntelligenceError(
            f"No valid predictions extracted. Predictions format: {predictions}"
        )

    return SentimentPrediction(
        label=top_label,
        score=top_score,
        scores_by_label=scores_by_label,
    )


class EmailIntelligenceService:
    """
    Convenience wrapper providing a single-call workflow for email analysis.
    """

    def __init__(
        self,
        candidate_labels: Iterable[str] | None = None,
        *,
        multi_label: bool = True,
        hypothesis_template: str | None = None,
    ):
        labels = candidate_labels if candidate_labels is not None else DEFAULT_EMAIL_ROUTING_LABELS
        self._candidate_labels = _normalize_labels(labels)
        self._multi_label = multi_label
        self._hypothesis_template = hypothesis_template

    def classify(self, text: str) -> ClassificationResult:
        return classify_email(
            text,
            self._candidate_labels,
            multi_label=self._multi_label,
            hypothesis_template=self._hypothesis_template,
        )

    def phishing(self, text: str) -> PhishingDetection:
        return detect_phishing(text)

    def sentiment(self, text: str) -> SentimentPrediction:
        return analyze_sentiment(text)

    def analyze_email(self, text: str) -> EmailInsights:
        """
        Run routing, phishing detection, and sentiment in a single call.
        """
        return EmailInsights(
            classification=self.classify(text),
            phishing=self.phishing(text),
            sentiment=self.sentiment(text),
        )


__all__ = [
    "EmailIntelligenceError",
    "ClassificationResult",
    "PhishingDetection",
    "SentimentPrediction",
    "EmailInsights",
    "DEFAULT_EMAIL_ROUTING_LABELS",
    "EmailIntelligenceService",
    "classify_email",
    "detect_phishing",
    "analyze_sentiment",
]
