from __future__ import annotations

from uuid import UUID
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from ..core.logging import get_logger
from ..dependencies import get_siembra_service, get_pdf_generator
from ..dto.siembra import (
    BulkSiembraRequest,
    BulkSiembraResponse,
    RecommendationPdfRequest,
    SiembraHistoryItem,
    SiembraHistoryResponse,
)
from ..services.siembra.recommendation_service import SiembraRecommendationService
from ..services.pdf_generator import RecommendationPDFGenerator, normalise_pdf_payload
from ..exceptions import CampaignNotFoundError


logger = get_logger("recommendations_controller")

router = APIRouter(prefix="/api/v1/recomendaciones", tags=["recomendaciones"])


@router.post(
    "/siembra",
    response_model=BulkSiembraResponse,
    status_code=status.HTTP_200_OK,
)
async def obtener_recomendacion_siembra(
    payload: BulkSiembraRequest,
    service: SiembraRecommendationService = Depends(get_siembra_service),
) -> BulkSiembraResponse:
    """Genera recomendaciones de siembra para uno o varios lotes."""
    logger.info(
        "Procesando recomendación de siembra",
        extra={
            "lotes": payload.lote_ids,
            "cultivo": payload.cultivo,
            "total_lotes": len(payload.lote_ids),
        }
    )

    try:
        response = await service.bulk_generate_recommendation(payload)
        return response

    except CampaignNotFoundError as exc:
        logger.warning(
            "Campaña requerida o inválida en recomendación de siembra",
            extra={"error": str(exc), "lotes": payload.lote_ids},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        logger.warning(
            "Error de validación en recomendación de siembra",
            extra={"error": str(exc), "lotes": payload.lote_ids},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación: {exc}",
        ) from exc

    except Exception as exc:
        logger.exception(
            "Error inesperado al generar recomendación de siembra",
            extra={"lotes": payload.lote_ids},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo generar la recomendación de siembra",
        ) from exc


@router.get(
    "/siembra/historial",
    response_model=SiembraHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def listar_historial_siembra(
    cliente_id: Optional[UUID] = Query(
        default=None,
        description="Filtra por cliente asociado a la recomendación"
    ),
    lote_id: Optional[UUID] = Query(
        default=None,
        description="Filtra por lote"
    ),
    cultivo: Optional[str] = Query(
        default=None,
        description="Filtra por cultivo"
    ),
    campana: Optional[str] = Query(
        default=None,
        description="Filtra por campaña agrícola (formato AAAA/AAAA)"
    ),
    service: SiembraRecommendationService = Depends(get_siembra_service),
) -> SiembraHistoryResponse:
    """Devuelve el historial de recomendaciones de siembra filtrado."""

    try:
        historial = await service.get_history(
            cliente_id=str(cliente_id) if cliente_id else None,
            lote_id=str(lote_id) if lote_id else None,
            cultivo=cultivo,
            campana=campana,
        )
    except ValueError as exc:
        logger.warning(
            "Filtros inválidos al consultar historial de siembra",
            extra={"error": str(exc)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return SiembraHistoryResponse(total=len(historial), items=historial)


@router.get(
    "/siembra/{prediccion_id}/pdf",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def descargar_pdf_recomendacion(
    prediccion_id: UUID,
    service: SiembraRecommendationService = Depends(get_siembra_service),
    pdf_generator: RecommendationPDFGenerator = Depends(get_pdf_generator),
) -> StreamingResponse:
    """Descarga el PDF asociado a una recomendación previamente generada."""
    try:
        history_entry = await service.get_history_entry(prediccion_id=str(prediccion_id))
        recommendation_data = _history_item_to_recommendation(history_entry)
        
        # Obtener nombre del lote
        lote_label = await _get_lote_label(service, str(history_entry.lote_id))
        metadata = {"lote_label": lote_label} if lote_label else {}
        
        payload = normalise_pdf_payload(recommendation=recommendation_data, metadata=metadata)
        pdf_bytes = pdf_generator.build_pdf(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Error generando PDF de recomendaci��n", extra={"id": str(prediccion_id)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo generar el PDF solicitado",
        ) from exc

    filename = _build_pdf_filename(
        lote_id=recommendation_data.get("lote_id"),
        campana=recommendation_data.get("datos_entrada", {}).get("campana"),
    )
    return _stream_pdf(pdf_bytes, filename)


@router.post(
    "/siembra/pdf",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
async def generar_pdf_desde_payload(
    payload: RecommendationPdfRequest,
    pdf_generator: RecommendationPDFGenerator = Depends(get_pdf_generator),
) -> StreamingResponse:
    """Genera un PDF en base a una recomendaci��n reci��n calculada."""
    try:
        recommendation_data = payload.recomendacion.model_dump(mode="json")
        pdf_payload = normalise_pdf_payload(
            recommendation=recommendation_data,
            metadata=payload.metadata,
        )
        pdf_bytes = pdf_generator.build_pdf(pdf_payload)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Error generando PDF desde payload")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo generar el PDF solicitado",
        ) from exc

    filename = _build_pdf_filename(
        lote_id=recommendation_data.get("lote_id"),
        campana=recommendation_data.get("datos_entrada", {}).get("campana"),
    )
    return _stream_pdf(pdf_bytes, filename)


def _stream_pdf(content: bytes, filename: str) -> StreamingResponse:
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Cache-Control": "no-store",
    }
    return StreamingResponse(
        BytesIO(content),
        media_type="application/pdf",
        headers=headers,
    )


def _build_pdf_filename(*, lote_id: Optional[str], campana: Optional[str]) -> str:
    lote_component = _safe_filename_component(lote_id or "recomendacion")
    campana_component = _safe_filename_component(campana or datetime.now(timezone.utc).strftime("%Y%m%d"))
    return f"recomendacion-{lote_component}-{campana_component}.pdf"


def _safe_filename_component(value: str) -> str:
    return "".join(char for char in value if char.isalnum() or char in ("-", "_")).lower() or "archivo"


async def _get_lote_label(service: SiembraRecommendationService, lote_id: str) -> Optional[str]:
    """Obtiene el nombre del lote desde el sistema principal.
    
    Args:
        service: Servicio de recomendaciones
        lote_id: ID del lote
        
    Returns:
        Nombre del lote o None si no se puede obtener
    """
    try:
        lote_data = await service.main_system_client.get_lote_data(lote_id)
        return lote_data.get("nombre") if lote_data else None
    except Exception as exc:
        logger.warning(
            "Error obteniendo nombre del lote",
            extra={"lote_id": lote_id, "error": str(exc)}
        )
        return None


def _history_item_to_recommendation(item: SiembraHistoryItem) -> Dict[str, Any]:
    datos_entrada = dict(item.datos_entrada or {})
    fecha_generacion = item.fecha_creacion or datetime.now(timezone.utc)

    return {
        "lote_id": str(item.lote_id),
        "tipo_recomendacion": "siembra",
        "prediccion_id": str(item.id),
        "recomendacion_principal": item.recomendacion_principal.model_dump(mode="json"),
        "alternativas": item.alternativas,
        "nivel_confianza": item.nivel_confianza or item.recomendacion_principal.confianza,
        "costos_estimados": {},
        "fecha_generacion": fecha_generacion.isoformat(),
        "cultivo": item.cultivo,
        "datos_entrada": datos_entrada,
    }
