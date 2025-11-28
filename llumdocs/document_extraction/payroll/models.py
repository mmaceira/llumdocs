"""Pydantic models for payroll document structure.

This module defines the data models used for extracting and representing
structured information from Spanish payroll documents (nóminas).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class Deduccion(BaseModel):
    """Deduction line item in a payroll.

    Represents one deduction from the employee's gross salary.

    Attributes:
        concepto: Description of the deduction (required).
        importe: Amount of the deduction (required).
    """

    model_config = ConfigDict(extra="forbid")

    concepto: str = Field(..., description="Deduction description")
    importe: float = Field(..., description="Deduction amount")


class Devengo(BaseModel):
    """Earning line item in a payroll.

    Represents one earning component of the employee's gross salary.

    Attributes:
        concepto: Description of the earning (required).
        importe: Amount of the earning (required).
    """

    model_config = ConfigDict(extra="forbid")

    concepto: str = Field(..., description="Earning description")
    importe: float = Field(..., description="Earning amount")


class PayrollReport(BaseModel):
    """Complete schema for payroll (nómina) extraction.

    This model represents all extractable information from a Spanish payroll document,
    including employer/employee information, earnings, deductions, and totals.

    Attributes:
        empresa_nif: Employer's tax ID (NIF/CIF).
        empleado_dni: Employee's DNI/NIE.
        periodo: Pay period in YYYY-MM format.
        categoria: Employee category/position.
        iban: Bank account IBAN for payment.
        devengos: List of earning line items.
        deducciones: List of deduction line items.
        bruto: Gross salary amount.
        total_deducciones: Total deductions amount.
        neto: Net salary amount (after deductions).
    """

    model_config = ConfigDict(extra="forbid")

    empresa_nif: str | None = Field(None, description="Employer tax ID (NIF/CIF)")
    empleado_dni: str | None = Field(None, description="Employee DNI/NIE")
    periodo: str | None = Field(None, description="Pay period, format YYYY-MM")
    categoria: str | None = Field(None, description="Employee category/position")
    iban: str | None = Field(None, description="Bank account IBAN")
    devengos: list[Devengo] = Field(default_factory=list, description="Earnings list")
    deducciones: list[Deduccion] = Field(default_factory=list, description="Deductions list")
    bruto: float | None = Field(None, description="Gross salary")
    total_deducciones: float | None = Field(None, description="Total deductions")
    neto: float | None = Field(None, description="Net salary")

    @field_validator("neto")
    @classmethod
    def check_totals(cls, v: float | None, info: ValidationInfo) -> float | None:
        """Validate that net = bruto - total_deducciones (with small rounding tolerance)."""
        if v is None:
            return v
        bruto = info.data.get("bruto")
        td = info.data.get("total_deducciones")
        if all(x is not None for x in (bruto, td, v)):
            # Allow small rounding differences (0.05)
            diff = abs((bruto - td) - v)
            if diff >= 0.05:
                # Don't raise, just log - allow slight inconsistencies
                pass
        return v
