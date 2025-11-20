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


@dataclass(frozen=True)
class EmailInsights:
    classification: ClassificationResult
    phishing: PhishingDetection
    sentiment: SentimentPrediction


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
    """Get mapping from model's LABEL_X format to human-readable labels."""
    global _PHISHING_LABEL_MAP
    if _PHISHING_LABEL_MAP is None:
        try:
            config = AutoConfig.from_pretrained(PHISHING_MODEL_ID)
            id2label = getattr(config, "id2label", {})
            if id2label:
                _PHISHING_LABEL_MAP = {}
                for label_id, label_name in id2label.items():
                    # Try to find a readable name - common patterns:
                    # LABEL_0 -> safe/legitimate, LABEL_1 -> phishing/spam
                    if label_name.startswith("LABEL_"):
                        # Default mapping based on common phishing model structure
                        # Most phishing models are binary: safe vs phishing
                        if label_id == 0:
                            _PHISHING_LABEL_MAP[label_name] = "safe"
                        elif label_id == 1:
                            _PHISHING_LABEL_MAP[label_name] = "phishing"
                        else:
                            # For additional labels beyond binary, use a generic name
                            # but we'll filter these out in the UI if they have zero scores
                            _PHISHING_LABEL_MAP[label_name] = f"class_{label_id}"
                    else:
                        # Already readable - use as-is
                        _PHISHING_LABEL_MAP[label_name] = label_name
            else:
                # Fallback: create default mapping for binary classification
                _PHISHING_LABEL_MAP = {
                    "LABEL_0": "safe",
                    "LABEL_1": "phishing",
                }
        except Exception:  # noqa: BLE001
            # Fallback if config loading fails
            _PHISHING_LABEL_MAP = {
                "LABEL_0": "safe",
                "LABEL_1": "phishing",
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
    text_value = _normalize_text(text)

    pipeline_runner: Pipeline | None = None
    try:
        pipeline_runner = _get_phishing_pipeline()
        raw = pipeline_runner(
            text_value,
            return_all_scores=True,
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
                return_all_scores=True,
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

    # Map model labels to human-readable labels
    ordered = {}
    for item in scores:
        if "label" in item and "score" in item:
            model_label = item["label"]
            readable_label = label_map.get(model_label, model_label)
            ordered[readable_label] = float(item["score"])

    if not ordered:
        raise EmailIntelligenceError("Phishing model returned no labels.")

    best_label = max(ordered, key=ordered.get)
    return PhishingDetection(label=best_label, score=ordered[best_label], scores_by_label=ordered)


def analyze_sentiment(text: str) -> SentimentPrediction:
    """
    Run multilingual sentiment analysis (positive/neutral/negative).
    """
    text_value = _normalize_text(text)

    pipeline_runner: Pipeline | None = None
    try:
        pipeline_runner = _get_sentiment_pipeline()
        prediction = pipeline_runner(text_value)[0]
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
            prediction = pipeline_runner(text_value)[0]
        else:
            raise EmailIntelligenceError(str(exc)) from exc
    except OSError as exc:
        raise EmailIntelligenceError(str(exc)) from exc
    finally:
        if pipeline_runner is not None:
            _release_pipeline("_SENTIMENT_PIPELINE")

    return SentimentPrediction(label=str(prediction["label"]), score=float(prediction["score"]))


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
