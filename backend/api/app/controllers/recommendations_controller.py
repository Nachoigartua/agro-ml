from __future__ import annotations

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.logging import get_logger
from ..dependencies import get_siembra_service
from ..dto.siembra import (
    BulkSiembraRequest,
    BulkSiembraResponse,
    SiembraHistoryResponse,
)
from ..services.siembra.recommendation_service import SiembraRecommendationService
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
