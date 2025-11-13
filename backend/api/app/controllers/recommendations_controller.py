from __future__ import annotations

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from ..core.logging import get_logger
from ..dependencies import get_siembra_service
from ..dto.siembra import (
    SiembraHistoryResponse,
    SiembraRecommendationResponse,
    SiembraRequest,
)
from ..services.siembra.recommendation_service import SiembraRecommendationService
from ..services.pdf_generator import PDFGeneratorService
from ..exceptions import CampaignNotFoundError


logger = get_logger("recommendations_controller")

router = APIRouter(prefix="/api/v1/recomendaciones", tags=["recomendaciones"])
pdf_service = PDFGeneratorService()


@router.post(
    "/siembra",
    response_model=SiembraRecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def obtener_recomendacion_siembra(
    payload: SiembraRequest,
    service: SiembraRecommendationService = Depends(get_siembra_service),
) -> SiembraRecommendationResponse:
    """Genera una recomendación de siembra."""
    logger.info(
        "Procesando recomendación de siembra",
        extra={"lote_id": str(payload.lote_id), "cultivo": payload.cultivo}
    )

    try:
        response = await service.generate_recommendation(payload)
        return response
        
    except CampaignNotFoundError as exc:
        logger.warning(
            "Campaña requerida o inválida en recomendación de siembra",
            extra={"error": str(exc), "lote_id": payload.lote_id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
        
    except ValueError as exc:
        logger.warning(
            "Error de validación en recomendación de siembra",
            extra={"error": str(exc), "lote_id": payload.lote_id}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación: {exc}",
        ) from exc
        
    except Exception as exc:
        logger.exception(
            "Error inesperado al generar recomendación de siembra",
            extra={"lote_id": payload.lote_id}
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


@router.post(
    "/siembra/{prediccion_id}/pdf",
    status_code=status.HTTP_200_OK,
)
async def descargar_recomendacion_pdf(
    prediccion_id: UUID,
    service: SiembraRecommendationService = Depends(get_siembra_service),
) -> StreamingResponse:
    """Descarga el PDF de una recomendación de siembra específica.
    
    Args:
        prediccion_id: ID de la predicción/recomendación
        service: Servicio de recomendaciones
        
    Returns:
        PDF en formato StreamingResponse
        
    Raises:
        HTTPException: Si la predicción no se encuentra o hay error al generar PDF
    """
    try:
        # Obtener recomendación y datos de lote directamente desde el servicio (sin bucles)
        recommendation, lote_info = await service.get_recommendation_for_pdf(str(prediccion_id))

        if not recommendation or not lote_info:
            logger.warning(
                "Predicción no encontrada para PDF",
                extra={"prediccion_id": str(prediccion_id)}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recomendación no encontrada",
            )
        
        # Generar PDF
        pdf_bytes = pdf_service.generate_recommendation_pdf(
            recommendation=recommendation,
            lote_info=lote_info,
        )
        
        logger.info(
            "PDF descargado exitosamente",
            extra={
                "prediccion_id": str(prediccion_id),
                "lote_id": recommendation.lote_id,
            }
        )
        
        # Retornar PDF como descarga (StreamingResponse permite enviar binarios sin buffer completo).
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=recomendacion_{prediccion_id}_{recommendation.cultivo}.pdf"
            },
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Error inesperado al generar PDF de recomendación",
            extra={"prediccion_id": str(prediccion_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo generar el PDF de la recomendación",
        ) from exc
