"""Herramientas para generar reportes en PDF de recomendaciones."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any, Iterable, Mapping, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@dataclass(frozen=True)
class PdfPayload:
    """Estructura normalizada para construir el PDF."""

    recommendation: Mapping[str, Any]
    metadata: Mapping[str, Any]


class RecommendationPDFGenerator:
    """Genera documentos PDF a partir de una recomendación."""

    def __init__(self) -> None:
        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="SectionTitle",
                fontSize=12,
                leading=14,
                spaceAfter=6,
                textColor="#1a237e",
                uppercase=False,
            )
        )
        styles.add(
            ParagraphStyle(
                name="SmallLabel",
                fontSize=8,
                textColor="#546e7a",
            )
        )
        self._styles = styles

    def build_pdf(self, payload: PdfPayload) -> bytes:
        """Genera un PDF y devuelve los bytes del archivo."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story: list[Any] = []
        recommendation = payload.recommendation
        metadata = payload.metadata

        story.extend(self._build_header(recommendation, metadata))
        story.append(Spacer(1, 0.5 * cm))
        story.extend(self._build_input_section(recommendation))
        story.append(Spacer(1, 0.4 * cm))
        story.extend(self._build_recommendation_section(recommendation))
        story.append(Spacer(1, 0.4 * cm))
        alt_flowables = self._build_alternatives_section(recommendation)
        if alt_flowables:
            story.extend(alt_flowables)
            story.append(Spacer(1, 0.4 * cm))
        costs = self._build_cost_section(recommendation)
        if costs:
            story.extend(costs)
            story.append(Spacer(1, 0.4 * cm))
        meta_notes = self._build_metadata_section(recommendation)
        if meta_notes:
            story.extend(meta_notes)

        doc.build(story)
        return buffer.getvalue()

    def _build_header(
        self,
        recommendation: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> list[Any]:
        """Crea el encabezado del PDF."""
        lote_label = metadata.get("lote_label") or recommendation.get("lote_id", "Lote sin nombre")
        cultivo = str(recommendation.get("cultivo", "—")).title()
        generated_at = self._format_datetime(recommendation.get("fecha_generacion"))
        requested_at = self._format_datetime(
            recommendation.get("datos_entrada", {}).get("fecha_consulta")
        )
        campaign = recommendation.get("datos_entrada", {}).get("campana") or "No especificada"

        title = Paragraph("Informe de recomendación agronómica", self._styles["Title"])
        subtitle = Paragraph(
            f"{lote_label} · Cultivo {cultivo} · Campaña {campaign}",
            self._styles["Heading4"],
        )
        caption = Paragraph(
            f"Solicitada el {requested_at or '—'} · Generada el {generated_at or '—'}",
            self._styles["SmallLabel"],
        )

        summary_data = [
            ["Lote", lote_label],
            ["Cultivo", cultivo],
            ["Nivel de confianza", self._format_confidence(recommendation.get("nivel_confianza"))],
        ]
        summary_table = Table(summary_data, colWidths=[4 * cm, 10 * cm])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#263238")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        return [title, subtitle, caption, Spacer(1, 0.25 * cm), summary_table, HRFlowable(width="100%")]

    def _build_input_section(self, recommendation: Mapping[str, Any]) -> list[Any]:
        datos = recommendation.get("datos_entrada") or {}
        if not isinstance(datos, Mapping):
            datos = {}

        rows = [
            ("Cliente", datos.get("cliente_id", "—")),
            ("Campaña", datos.get("campana", "—")),
            ("Fecha de consulta", self._format_datetime(datos.get("fecha_consulta")) or "—"),
        ]
        additional_entries = [
            (key.replace("_", " ").title(), value)
            for key, value in datos.items()
            if key not in {"cliente_id", "campana", "fecha_consulta"} and value not in (None, "")
        ]
        additional_entries.sort(key=lambda pair: pair[0])
        rows.extend(additional_entries)

        table = Table(rows, colWidths=[5 * cm, 9 * cm])
        table.setStyle(self._table_style())

        return [
            Paragraph("Datos proporcionados por el usuario", self._styles["SectionTitle"]),
            table,
        ]

    def _build_recommendation_section(self, recommendation: Mapping[str, Any]) -> list[Any]:
        principal = recommendation.get("recomendacion_principal") or {}
        riesgos = principal.get("riesgos") or []
        ventana = principal.get("ventana") or []
        ventana_fmt = " · ".join(filter(None, [self._format_date(v) for v in ventana]))
        confidence = self._format_confidence(principal.get("confianza"))

        rows = [
            ("Fecha óptima", self._format_date(principal.get("fecha_optima")) or "—"),
            ("Ventana recomendada", ventana_fmt or "—"),
            ("Confianza", confidence),
        ]
        table = Table(rows, colWidths=[5 * cm, 9 * cm])
        table.setStyle(self._table_style())

        flowables: list[Any] = [
            Paragraph("Recomendación principal", self._styles["SectionTitle"]),
            table,
        ]

        if riesgos:
            riesgos_list = "<br/>".join(f"• {riesgo}" for riesgo in riesgos)
            flowables.append(Spacer(1, 0.2 * cm))
            flowables.append(Paragraph(f"<b>Riesgos detectados</b><br/>{riesgos_list}", self._styles["BodyText"]))

        return flowables

    def _build_alternatives_section(self, recommendation: Mapping[str, Any]) -> list[Any]:
        alternativas = recommendation.get("alternativas") or []
        if not isinstance(alternativas, Sequence) or not alternativas:
            return []

        header = Paragraph("Escenarios alternativos", self._styles["SectionTitle"])
        rows = [["Fecha", "Ventana", "Confianza", "Escenario"]]
        for alternativa in alternativas:
            ventana = alternativa.get("ventana") or []
            ventana_txt = " · ".join(filter(None, [self._format_date(v) for v in ventana]))
            scenario = alternativa.get("escenario_climatico", {}) or {}
            scen_txt = scenario.get("nombre") or scenario.get("descripcion") or "—"
            rows.append(
                [
                    self._format_date(alternativa.get("fecha")) or "—",
                    ventana_txt or "—",
                    self._format_confidence(alternativa.get("confianza")),
                    scen_txt,
                ]
            )

        table = Table(rows, colWidths=[3 * cm, 4 * cm, 3 * cm, 4 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3f2fd")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0d47a1")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
                ]
            )
        )

        return [header, table]

    def _build_cost_section(self, recommendation: Mapping[str, Any]) -> list[Any]:
        costos = recommendation.get("costos_estimados") or {}
        if not isinstance(costos, Mapping) or not costos:
            return []

        rows = [["Concepto", "Monto estimado (USD)"]]
        for key, value in costos.items():
            rows.append([key.replace("_", " ").title(), f"{float(value):,.2f}"])

        table = Table(rows, colWidths=[7 * cm, 7 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ede7f6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#4527a0")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
                ]
            )
        )

        return [Paragraph("Costos estimados", self._styles["SectionTitle"]), table]

    def _build_metadata_section(self, recommendation: Mapping[str, Any]) -> list[Any]:
        metadata = recommendation.get("metadata") or {}
        if not isinstance(metadata, Mapping) or not metadata:
            return []

        rows = [
            (key.replace("_", " ").title(), str(value))
            for key, value in metadata.items()
            if value not in (None, "")
        ]
        rows.sort(key=lambda pair: pair[0])
        table = Table(rows, colWidths=[5 * cm, 9 * cm])
        table.setStyle(self._table_style())

        return [Paragraph("Metadatos adicionales", self._styles["SectionTitle"]), table]

    def _table_style(self) -> TableStyle:
        return TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ]
        )

    @staticmethod
    def _format_confidence(value: Any) -> str:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return "—"
        return f"{num * 100:,.0f}%"

    @staticmethod
    def _format_date(value: Any) -> str | None:
        if not value:
            return None
        if isinstance(value, str) and "-" in value and len(value.split("-")) == 3:
            return value.replace("-", "/")
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return str(value)
        return parsed.strftime("%d/%m/%Y")

    @staticmethod
    def _format_datetime(value: Any) -> str | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return str(value)
        return parsed.strftime("%d/%m/%Y %H:%M")


def normalise_pdf_payload(
    *,
    recommendation: Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
) -> PdfPayload:
    """Crea un PdfPayload asegurando estructuras predecibles."""
    return PdfPayload(
        recommendation=recommendation,
        metadata=metadata or {},
    )
