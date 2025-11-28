"""Pydantic models for delivery note document structure.

This module defines the data models used for extracting and representing
structured information from delivery note documents.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProductoLinea(BaseModel):
    """Single product or service line item in a delivery note.

    Represents one line item from the products/services table in a delivery note.
    All fields except 'producto' and 'cantidad' are optional.

    Attributes:
        producto: Product or service name/code (required).
        descripcion: Detailed description of the product/service.
        cantidad: Quantity of product units (required).
        unidad: Unit of measurement (e.g., "ud", "kg", "m").
        precio_unitario: Unit price in the document's currency.
        importe_linea: Total amount for this line (quantity × unit price).
    """

    model_config = ConfigDict(extra="forbid")

    producto: str = Field(..., description="Product or service name/code")
    descripcion: str | None = Field(None, description="Detailed description")
    cantidad: float = Field(..., description="Quantity of product units")
    unidad: str | None = Field(None, description="Unit of measurement")
    precio_unitario: float | None = Field(None, description="Unit price")
    importe_linea: float | None = Field(None, description="Total line amount")


class AlbaranReport(BaseModel):
    """Complete schema for delivery note/invoice extraction.

    This model represents all extractable information from a delivery note document,
    including document metadata, supplier information, product lines, and financial totals.

    Attributes:
        numero_albaran: Unique delivery note number (required).
        fecha_albaran: Date of document in YYYY-MM-DD format (required).
        categoria_gasto: Expense category classification.
        fecha_registro: Registration date in YYYY-MM-DD format.
        moneda: Currency code (defaults to "EUR").
        estado: Document status (e.g., "Pendiente", "Pagado").
        fichero_datalake: File reference for data lake storage.
        nombre_empresa: Supplier company name (required).
        nif_cif: Tax ID (NIF/CIF) of the supplier.
        direccion: Supplier address.
        codigo_postal: Postal code.
        poblacion: City name.
        productos: List of product/service line items (required).
        base_imponible: Total amount before taxes (required).
        porcentaje_impuestos: Tax percentage (e.g., 21.0 for 21% VAT).
        importe_impuestos: Tax amount in currency.
        importe_con_impuestos: Total including taxes.
        porcentaje_retencion: Withholding tax percentage.
        importe_retencion: Withholding tax amount.
        total_albaran: Final total amount (required).
    """

    model_config = ConfigDict(extra="forbid")

    # Document data
    numero_albaran: str = Field(..., description="Unique delivery note number")
    fecha_albaran: str = Field(..., description="Date of document, format YYYY-MM-DD")
    categoria_gasto: str | None = Field(None, description="Expense category")
    fecha_registro: str | None = Field(None, description="Registration date, format YYYY-MM-DD")
    moneda: str = Field("EUR", description="Currency code")
    estado: str | None = Field(None, description="Status")
    fichero_datalake: str | None = Field(None, description="File reference")

    # Supplier data
    nombre_empresa: str = Field(..., description="Supplier company name")
    nif_cif: str | None = Field(None, description="Tax ID (NIF/CIF)")
    direccion: str | None = Field(None, description="Address")
    codigo_postal: str | None = Field(None, description="Postal code")
    poblacion: str | None = Field(None, description="City")

    # Products
    productos: list[ProductoLinea] = Field(..., description="List of products/services")

    # Financial
    base_imponible: float = Field(..., description="Total before taxes")
    porcentaje_impuestos: float | None = Field(None, description="Tax percentage")
    importe_impuestos: float | None = Field(None, description="Tax amount")
    importe_con_impuestos: float | None = Field(None, description="Total with taxes")
    porcentaje_retencion: float | None = Field(None, description="Withholding percentage")
    importe_retencion: float | None = Field(None, description="Withholding amount")
    total_albaran: float = Field(..., description="Final total amount")
