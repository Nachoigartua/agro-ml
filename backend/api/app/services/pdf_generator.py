"""Servicio para generar PDFs de recomendaciones de siembra."""
from __future__ import annotations

from io import BytesIO
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib import colors
from reportlab.pdfgen import canvas

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

        # Crear estilos personalizados
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a472a"),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#2d5a3d"),
            spaceAfter=8,
            spaceBefore=10,
            fontName="Helvetica-Bold",
        )

        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        )

        # Encabezado
        story.append(Paragraph("RECOMENDACIÓN DE SIEMBRA", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Información general
        story.append(Paragraph("INFORMACIÓN GENERAL", heading_style))
        general_data = [
            ["Cultivo:", recommendation.cultivo.upper()],
            ["Lote:", lote_info.get("nombre", recommendation.lote_id)],
            ["Campaña:", lote_info.get("campana", "—")],
            [
                "Fecha de consulta:",
                self._format_datetime(recommendation.fecha_generacion),
            ],
            [
                "Tipo de recomendación:",
                recommendation.tipo_recomendacion.upper(),
            ],
        ]
        general_table = Table(general_data, colWidths=[2 * inch, 3 * inch])
        general_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f5e9")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        story.append(general_table)
        story.append(Spacer(1, 0.2 * inch))

        # Datos de entrada del usuario
        story.append(Paragraph("DATOS INGRESADOS POR EL USUARIO", heading_style))
        entrada_data = self._build_input_table(recommendation.datos_entrada)
        entrada_table = Table(entrada_data, colWidths=[2 * inch, 3 * inch])
        entrada_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff3e0")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        story.append(entrada_table)
        story.append(Spacer(1, 0.2 * inch))

        # Recomendación principal
        story.append(
            Paragraph("RECOMENDACIÓN PRINCIPAL", heading_style)
        )
        rec_principal = recommendation.recomendacion_principal
        principal_text = f"""
        <b>Fecha óptima de siembra:</b> {self._format_date(rec_principal.fecha_optima)}<br/>
        <b>Ventana recomendada:</b> {self._format_date(rec_principal.ventana[0])} a {self._format_date(rec_principal.ventana[1])}<br/>
        <b>Nivel de confianza:</b> {rec_principal.confianza * 100:.1f}%<br/>
        """
        story.append(Paragraph(principal_text, normal_style))

        # Riesgos identificados
        if rec_principal.riesgos:
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("RIESGOS IDENTIFICADOS", heading_style))
            for riesgo in rec_principal.riesgos:
                story.append(Paragraph(f"• {riesgo}", normal_style))

        story.append(Spacer(1, 0.2 * inch))

        # Alternativas
        if recommendation.alternativas:
            story.append(Paragraph("ALTERNATIVAS CONSIDERADAS", heading_style))
            for i, alt in enumerate(recommendation.alternativas, 1):
                alt_text = f"""
                <b>Alternativa {i}:</b><br/>
                Fecha: {self._format_date(alt.get('fecha', '—'))}<br/>
                Ventana: {self._format_date(alt.get('ventana', ['—', '—'])[0])} a {self._format_date(alt.get('ventana', ['—', '—'])[1])}<br/>
                Confianza: {alt.get('confianza', 0) * 100:.1f}%<br/>
                """
                story.append(Paragraph(alt_text, normal_style))

                if alt.get("pros"):
                    story.append(Paragraph("<b>Ventajas:</b>", normal_style))
                    for pro in alt.get("pros", []):
                        story.append(Paragraph(f"✓ {pro}", normal_style))

                if alt.get("contras"):
                    story.append(Paragraph("<b>Desventajas:</b>", normal_style))
                    for contra in alt.get("contras", []):
                        story.append(Paragraph(f"✗ {contra}", normal_style))

                story.append(Spacer(1, 0.1 * inch))

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

    def _build_input_table(self, datos_entrada: Dict[str, Any]) -> List[List[str]]:
        """Construye tabla con los datos ingresados por el usuario.

        Args:
            datos_entrada: Diccionario de datos de entrada

        Returns:
            Lista de listas para la tabla
        """
        table_data = [["Campo", "Valor"]]

        # Mapear campos importantes
        field_labels = {
            "lote_id": "ID del Lote",
            "cultivo": "Cultivo",
            "campana": "Campaña",
            "fecha_consulta": "Fecha de Consulta",
            "cliente_id": "ID del Cliente",
        }

        for key, label in field_labels.items():
            value = datos_entrada.get(key)
            if value:
                if isinstance(value, datetime):
                    value = self._format_datetime(value)
                table_data.append([label, str(value)])

        return table_data

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
