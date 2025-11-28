"""Pydantic models for bank statement structure.

This module defines the data models used for extracting and representing
structured information from bank statements.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BankLine(BaseModel):
    """Single transaction line in a bank statement.

    Represents one transaction entry in the statement.

    Attributes:
        fecha: Transaction date in YYYY-MM-DD format (required).
        concepto: Transaction description (required).
        importe: Transaction amount (required). Negative for expenses, positive for income.
        saldo: Account balance after this transaction.
    """

    model_config = ConfigDict(extra="forbid")

    fecha: str = Field(..., description="Transaction date, format YYYY-MM-DD")
    concepto: str = Field(..., description="Transaction description")
    importe: float = Field(
        ..., description="Transaction amount (negative=expense, positive=income)"
    )
    saldo: float | None = Field(None, description="Account balance after transaction")


class BankStatement(BaseModel):
    """Complete schema for bank statement extraction.

    This model represents all extractable information from a bank statement,
    including account information, period, and transaction lines.

    Attributes:
        banco: Bank name.
        titular: Account holder name.
        iban: Account IBAN.
        periodo_desde: Statement period start date in YYYY-MM-DD format.
        periodo_hasta: Statement period end date in YYYY-MM-DD format.
        moneda: Currency code (defaults to "EUR").
        lineas: List of transaction lines.
        saldo_inicial: Opening balance.
        saldo_final: Closing balance.
    """

    model_config = ConfigDict(extra="forbid")

    banco: str | None = Field(None, description="Bank name")
    titular: str | None = Field(None, description="Account holder name")
    iban: str | None = Field(None, description="Account IBAN")
    periodo_desde: str | None = Field(None, description="Statement period start, format YYYY-MM-DD")
    periodo_hasta: str | None = Field(None, description="Statement period end, format YYYY-MM-DD")
    moneda: str = Field("EUR", description="Currency code")
    lineas: list[BankLine] = Field(default_factory=list, description="Transaction lines")
    saldo_inicial: float | None = Field(None, description="Opening balance")
    saldo_final: float | None = Field(None, description="Closing balance")
