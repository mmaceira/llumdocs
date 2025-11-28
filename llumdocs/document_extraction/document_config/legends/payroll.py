"""Legend generation for payroll documents."""

from __future__ import annotations

from ...payroll.models import PayrollReport


def make_payroll_legend(report: PayrollReport) -> list[str]:
    """Build legend text lines from a PayrollReport."""
    lines = []
    if report.empresa_nif:
        lines.append(f"Empresa NIF: {report.empresa_nif}")
    if report.empleado_dni:
        lines.append(f"Empleado DNI: {report.empleado_dni}")
    if report.periodo:
        lines.append(f"Período: {report.periodo}")
    if report.categoria:
        lines.append(f"Categoría: {report.categoria}")
    if report.iban:
        lines.append(f"IBAN: {report.iban}")
    if report.devengos:
        lines.append("")
        lines.append("Devengos:")
        for i, d in enumerate(report.devengos[:5], 1):
            lines.append(f"  {i}. {d.concepto}: {d.importe:.2f} EUR")
    if report.deducciones:
        lines.append("")
        lines.append("Deducciones:")
        for i, d in enumerate(report.deducciones[:5], 1):
            lines.append(f"  {i}. {d.concepto}: {d.importe:.2f} EUR")
    lines.append("")
    if report.bruto is not None:
        lines.append(f"Bruto: {report.bruto:.2f} EUR")
    if report.total_deducciones is not None:
        lines.append(f"Total deducciones: {report.total_deducciones:.2f} EUR")
    if report.neto is not None:
        lines.append(f"Neto: {report.neto:.2f} EUR")
    return lines
