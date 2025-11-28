"""Document extraction pipeline with LLM.

Components: core (framework), deliverynote/bank/payroll (models), document_config (configuration).
"""

from .unified_extractor import extract_document

__all__ = ["extract_document"]
