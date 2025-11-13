"""Servicio para generar PDFs de recomendaciones de siembra."""
from __future__ import annotations

from io import BytesIO
from datetime import datetime, date
from typing import Any, Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors

from ..core.logging import get_logger
from ..dto.siembra import SiembraRecommendationResponse


logger = get_logger("pdf_generator")


class PDFGeneratorService:
    """Servicio para generar PDFs profesionales de recomendaciones de siembra."""

    def __init__(self):
        """Inicializa el servicio de generación de PDFs."""
        self.page_width, self.page_height = A4
        self.margin = 0.5 * inch

    def generate_recommendation_pdf(
        self,
        recommendation: SiembraRecommendationResponse,
        lote_info: Dict[str, Any],
    ) -> bytes:
        """Genera un PDF con la recomendación de siembra completa.

        Args:
            recommendation: Respuesta de recomendación de siembra
            lote_info: Información adicional del lote

        Returns:
            Bytes del PDF generado
        """
        buffer = BytesIO()

        try:
            # Crear documento
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin,
            )

            # Construir elementos del documento
            story = self._build_pdf_story(recommendation, lote_info)

            # Generar PDF
            doc.build(story)

            pdf_data = buffer.getvalue()
            logger.info(
                "PDF generado exitosamente",
                extra={
                    "lote_id": recommendation.lote_id,
                    "cultivo": recommendation.cultivo,
                    "pdf_size_kb": len(pdf_data) / 1024,
                },
            )

            return pdf_data

        except Exception as exc:
            logger.exception(
                "Error al generar PDF de recomendación",
                extra={"lote_id": recommendation.lote_id},
            )
            raise

    def _build_pdf_story(
        self,
        recommendation: SiembraRecommendationResponse,
        lote_info: Dict[str, Any],
    ) -> List[Any]:
        """Construye los elementos del documento PDF.

        Args:
            recommendation: Recomendación de siembra
            lote_info: Información del lote

        Returns:
            Lista de elementos Platypus para el documento
        """
        styles = getSampleStyleSheet()
        story: List[Any] = []

        title_style = ParagraphStyle(
            "HeroTitle",
            parent=styles["Heading1"],
            fontSize=24,
            leading=30,
            textColor=colors.HexColor("#1a472a"),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName="Helvetica-Bold",
        )
        body_style = ParagraphStyle(
            "BodyLine",
            parent=styles["BodyText"],
            fontSize=12,
            leading=18,
            spaceAfter=6,
        )
        star_section_style = ParagraphStyle(
            "StarSection",
            parent=styles["Heading2"],
            fontSize=14,
            leading=20,
            textColor=colors.HexColor("#1a472a"),
            spaceAfter=12,
            fontName="Helvetica-Bold",
        )
        block_heading_style = ParagraphStyle(
            "BlockHeading",
            parent=styles["Heading3"],
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#2d5a3d"),
            spaceBefore=18,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )

        story.append(Paragraph("RECOMENDACIÓN DE SIEMBRA", title_style))

        campaign = (
            lote_info.get("campana")
            or recommendation.datos_entrada.get("campana")
            or "—"
        )
        lote_label = recommendation.lote_id or "—"
        fecha_generacion = self._format_datetime_for_pdf(
            recommendation.fecha_generacion
        )
        cultivo = recommendation.cultivo.title() if recommendation.cultivo else "—"

        meta_lines = [
            f"Campaña {campaign}",
            f"Lote: {lote_label}",
            f"Fecha de generación: {fecha_generacion}",
            f"Cultivo {cultivo}",
        ]
        for line in meta_lines:
            story.append(Paragraph(line, body_style))

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("⭐ Recomendación Principal", star_section_style))

        rec_principal = recommendation.recomendacion_principal
        story.append(
            Paragraph(
                f"Fecha óptima: {self._format_date(rec_principal.fecha_optima)}",
                body_style,
            )
        )
        story.append(
            Paragraph(
                (
                    "Ventana recomendada: "
                    f"{self._format_window(rec_principal.ventana)}"
                ),
                body_style,
            )
        )
        story.append(
            Paragraph(
                (
                    "Confianza del modelo: "
                    f"{rec_principal.confianza * 100:.1f}%"
                ),
                body_style,
            )
        )

        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph("RIESGOS IDENTIFICADOS", block_heading_style))
        riesgos = rec_principal.riesgos or []
        if riesgos:
            for riesgo in riesgos:
                story.append(Paragraph(riesgo, body_style))
        else:
            story.append(Paragraph("Sin riesgos identificados.", body_style))

        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph("ALTERNATIVAS CONSIDERADAS", block_heading_style))
        if recommendation.alternativas:
            for alt in recommendation.alternativas:
                alt_fecha = self._format_date(alt.get("fecha"))
                alt_window = self._format_window(alt.get("ventana", []))
                try:
                    alt_conf = float(alt.get("confianza", 0)) * 100
                except (TypeError, ValueError):
                    alt_conf = 0.0
                story.append(Paragraph(f"Fecha: {alt_fecha}", body_style))
                story.append(
                    Paragraph(
                        f"Ventana recomendada: {alt_window}",
                        body_style,
                    )
                )
                story.append(
                    Paragraph(
                        f"Confianza del modelo: {alt_conf:.1f}%",
                        body_style,
                    )
                )
                story.append(Spacer(1, 0.1 * inch))
        else:
            story.append(
                Paragraph(
                    "No se identificaron alternativas para esta recomendación.",
                    body_style,
                )
            )

        story.append(Spacer(1, 0.3 * inch))

        # Pie de página
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        story.append(Paragraph("___" * 20, footer_style))
        story.append(
            Paragraph(
                f"Documento generado: {self._format_datetime(datetime.now())}<br/>"
                "Agro ML - Sistema de Recomendaciones Agrícolas",
                footer_style,
            )
        )

        return story

    def _format_window(self, ventana: Any) -> str:
        """Devuelve un texto amigable para una ventana recomendada."""
        if (
            not ventana
            or not isinstance(ventana, (list, tuple))
            or len(ventana) < 2
        ):
            return "—"

        inicio = self._format_date(ventana[0])
        fin = self._format_date(ventana[1])

        if inicio == "—" and fin == "—":
            return "—"
        if inicio == fin:
            return inicio
        return f"{inicio} – {fin}"

    def _format_datetime_for_pdf(self, value: Any) -> str:
        """Formatea un datetime con el estilo solicitado."""
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y – %H:%M")

        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value)
                return parsed.strftime("%d/%m/%Y – %H:%M")
            except ValueError:
                return value

        return "—"

    @staticmethod
    def _format_date(date_value: Any) -> str:
        """Formatea una fecha para visualización.

        Args:
            date_value: Valor de fecha (string, datetime, etc.)

        Returns:
            Fecha formateada
        """
        if isinstance(date_value, date):
            return date_value.strftime("%d/%m/%Y")

        if isinstance(date_value, datetime):
            return date_value.strftime("%d/%m/%Y")

        if isinstance(date_value, str):
            # Intentar parsear diferentes formatos
            formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"]
            for fmt in formats:
                try:
                    parsed = datetime.strptime(date_value, fmt)
                    return parsed.strftime("%d/%m/%Y")
                except ValueError:
                    continue
            return date_value

        return "—"

    @staticmethod
    def _format_datetime(dt_value: Any) -> str:
        """Formatea un datetime para visualización.

        Args:
            dt_value: Valor de datetime

        Returns:
            Datetime formateado
        """
        if isinstance(dt_value, datetime):
            return dt_value.strftime("%d/%m/%Y %H:%M:%S")

        if isinstance(dt_value, str):
            try:
                parsed = datetime.fromisoformat(dt_value)
                return parsed.strftime("%d/%m/%Y %H:%M:%S")
            except (ValueError, AttributeError):
                return dt_value

        return "—"
