from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..clients.mock_main_system_client import MockMainSystemAPIClient
from ..dependencies import get_main_system_client
from ..dto.lotes import LoteItem, LotesListResponse
from ..core.logging import get_logger


logger = get_logger("lotes_controller")

router = APIRouter(prefix="/api/v1/lotes", tags=["lotes"])


@router.get("", response_model=LotesListResponse, status_code=status.HTTP_200_OK)
async def listar_lotes(
    client: MockMainSystemAPIClient = Depends(get_main_system_client),
) -> LotesListResponse:
    """Devuelve el listado de lotes con coordenadas para el mapa."""
    try:
        raw = await client.list_lotes()

        # raw puede ser un dict (mock) o una lista (API real). Normalizamos a lista de dicts
        lotes_iter = raw.values() if isinstance(raw, dict) else raw

        items: List[LoteItem] = []
        for lote in lotes_iter:
            ubic = lote.get("ubicacion") or {}
            try:
                items.append(
                    LoteItem(
                        lote_id=str(lote.get("lote_id")),
                        nombre=str(lote.get("nombre") or "lote"),
                        latitud=float(ubic.get("latitud")),
                        longitud=float(ubic.get("longitud")),
                    )
                )
            except Exception as exc:  # datos incompletos: lo omitimos y registramos
                logger.warning(
                    "Lote omitido por datos incompletos",
                    extra={"lote": lote, "error": str(exc)},
                )

        return LotesListResponse(total=len(items), items=items)

    except Exception as exc:
        logger.exception("Error al listar lotes", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudieron listar los lotes",
        ) from exc

