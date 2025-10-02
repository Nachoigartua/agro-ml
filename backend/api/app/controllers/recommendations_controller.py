import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_siembra_service
from ..dto.siembra import SiembraRecommendationResponse, SiembraRequest
from ..services.siembra_service import SiembraRecommendationService


logger = logging.getLogger("agro_ml.recommendations")

router = APIRouter(prefix="/api/v1/recomendaciones", tags=["recomendaciones"])


@router.post(
    "/siembra",
    response_model=SiembraRecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def obtener_recomendacion_siembra(
    payload: SiembraRequest,
    service: SiembraRecommendationService = Depends(get_siembra_service),
) -> SiembraRecommendationResponse:
    """Genera una recomendacion de siembra."""
    logger.info(
        "Procesando recomendacion de siembra",
        extra={"lote_id": str(payload.lote_id), "cultivo": payload.cultivo},
    )

    try:
        response = await service.generate_recommendation(payload)
        logger.info(
            "Recomendacion de siembra generada",
            extra={
                "lote_id": str(response.lote_id),
                "confianza": response.nivel_confianza,
            },
        )
        return response
    except ValueError as exc:
        logger.warning(
            "Error de validacion en recomendacion de siembra",
            extra={"error": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Error inesperado al generar recomendacion de siembra")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo generar la recomendacion de siembra",
        ) from exc
