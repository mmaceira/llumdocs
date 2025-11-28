"""Legend generation for bank statement documents."""

from __future__ import annotations

from ...bank.models import BankStatement


def make_bank_legend(report: BankStatement) -> list[str]:
    """Build legend text lines from a BankStatement."""
    lines = []
    if report.banco:
        lines.append(f"Banco: {report.banco}")
    if report.titular:
        lines.append(f"Titular: {report.titular}")
    if report.iban:
        lines.append(f"IBAN: {report.iban}")
    if report.periodo_desde and report.periodo_hasta:
        lines.append(f"Período: {report.periodo_desde} a {report.periodo_hasta}")
    if report.saldo_inicial is not None:
        lines.append(f"Saldo inicial: {report.saldo_inicial:.2f} {report.moneda}")
    if report.lineas:
        lines.append("")
        lines.append("Transacciones:")
        for i, linea in enumerate(report.lineas[:10], 1):
            sign = "+" if linea.importe >= 0 else ""
            lines.append(f"  {i}. {linea.fecha}: {sign}{linea.importe:.2f} - {linea.concepto[:40]}")
    if report.saldo_final is not None:
        lines.append("")
        lines.append(f"Saldo final: {report.saldo_final:.2f} {report.moneda}")
    return lines
