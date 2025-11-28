"""Unified document type configuration for extraction and visualization."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from ..albaran.models import AlbaranReport
from ..bank.models import BankStatement
from ..payroll.models import PayrollReport
from .legends.albaran import make_albaran_legend
from .legends.bank import make_bank_legend
from .legends.payroll import make_payroll_legend
from .redaction.default import default_redact
from .redaction.payroll import redact_payroll


class DocumentConfig:
    """Configuration for a document type (model, prompts, text limit, legend, redaction)."""

    def __init__(
        self,
        model_class: type[BaseModel],
        system_prompt: str,
        user_prompt_template: str,
        text_limit: int | None = None,
        make_legend_lines: Callable[[BaseModel], list[str]] | None = None,
        redact_lines: Callable[[list[str]], list[str]] | None = None,
    ):
        self.model_class = model_class
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.text_limit = text_limit
        self.make_legend_lines = make_legend_lines
        self.redact_lines = redact_lines


# Document type configurations
DOCUMENT_CONFIGS: dict[str, DocumentConfig] = {
    "deliverynote": DocumentConfig(
        model_class=AlbaranReport,
        system_prompt=(
            "Extract structured information from delivery note text. "
            "Return ONLY a JSON object matching the schema, no markdown or explanations."
        ),
        user_prompt_template=(
            "Extract information from this delivery note document:\n\n{text}\n\n"
            "Return a flat JSON object with fields at root level (not nested). "
            "Fields should include: numero_albaran, fecha_albaran, nombre_empresa, "
            "productos (array), base_imponible, total_albaran, etc."
        ),
        make_legend_lines=make_albaran_legend,
        redact_lines=default_redact,
    ),
    "bank": DocumentConfig(
        model_class=BankStatement,
        system_prompt=(
            "Extraes campos de un extracto bancario español. "
            "Devuelve SOLO JSON válido para el esquema."
        ),
        user_prompt_template=(
            "Extrae información de este extracto bancario:\n\n{text}\n\n"
            "Devuelve campos: banco, titular, iban, periodo_desde, periodo_hasta, "
            "moneda, lineas (lista de transacciones con fecha, concepto, importe "
            "(negativo para gastos, positivo para ingresos), saldo opcional), "
            "saldo_inicial, saldo_final. Si un campo no está, pon null."
        ),
        text_limit=40000,
        make_legend_lines=make_bank_legend,
        redact_lines=default_redact,
    ),
    "payroll": DocumentConfig(
        model_class=PayrollReport,
        system_prompt=(
            "Extraes campos de una nómina española. Devuelve SOLO JSON válido para el esquema."
        ),
        user_prompt_template=(
            "Extrae información de esta nómina:\n\n{text}\n\n"
            "Devuelve campos: empresa_nif, empleado_dni, periodo (YYYY-MM), categoria, "
            "iban, devengos (lista con concepto e importe), deducciones (lista con "
            "concepto e importe), bruto, total_deducciones, neto. "
            "Si un campo no está, pon null."
        ),
        text_limit=40000,
        make_legend_lines=make_payroll_legend,
        redact_lines=redact_payroll,
    ),
}


def get_config(doc_type: str) -> DocumentConfig:
    """Get configuration for a document type. Raises ValueError if not found."""
    if doc_type not in DOCUMENT_CONFIGS:
        raise ValueError(
            f"Unknown doc_type: {doc_type}. Available types: {', '.join(DOCUMENT_CONFIGS.keys())}"
        )
    return DOCUMENT_CONFIGS[doc_type]
