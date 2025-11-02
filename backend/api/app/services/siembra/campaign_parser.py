"""Parseador y validador de campañas agrícolas."""
from __future__ import annotations

import re

from ...core.logging import get_logger
from ...exceptions import CampaignNotFoundError


logger = get_logger("siembra.campaign_parser")


class CampaignParser:
    """Parsea y valida el formato de campañas agrícolas."""

    # Formato esperado: AAAA/AAAA (ej: 2024/2025)
    CAMPAIGN_PATTERN = re.compile(r"^(\d{4})/(\d{4})$")
    YEAR_PATTERN = re.compile(r"^(?:19|20)\d{2}$")

    @classmethod
    def parse_target_year(cls, campana: str) -> int:
        """Extrae el año objetivo de una campaña.
        
        Args:
            campana: String de campaña en formato AAAA/AAAA
            
        Returns:
            Año objetivo (segundo año de la campaña)
            
        Raises:
            CampaignNotFoundError: Si la campaña es inválida
        """
        campana_clean = (campana or "").strip()
        
        if not campana_clean:
            raise CampaignNotFoundError(
                "El campo 'campana' es requerido y no puede estar vacío"
            )

        # Validar formato completo
        match = cls.CAMPAIGN_PATTERN.match(campana_clean)
        if not match:
            raise CampaignNotFoundError(
                f"El campo 'campana' debe tener formato AAAA/AAAA, "
                f"recibido: '{campana_clean}'"
            )

        year1_str, year2_str = match.groups()

        # Validar que ambos años sean válidos
        if not cls.YEAR_PATTERN.match(year2_str):
            raise CampaignNotFoundError(
                f"El segundo año de la campaña es inválido: '{year2_str}'"
            )

        # Parsear año objetivo (segundo año)
        try:
            target_year = int(year2_str)
        except ValueError as exc:
            # Este caso nunca debería ocurrir debido a la validación regex
            raise CampaignNotFoundError(
                f"Error al parsear el año objetivo: '{year2_str}'"
            ) from exc

        # Validación adicional: year2 debe ser year1 + 1
        try:
            year1 = int(year1_str)
            if year2_str != str(year1 + 1):
                logger.warning(
                    "Campaña con años no consecutivos",
                    extra={"campana": campana_clean, "year1": year1, "year2": target_year}
                )
        except ValueError:
            pass  # Si year1 no parsea, solo logueamos

        return target_year

    @classmethod
    def validate_campaign(cls, campana: str) -> bool:
        """Valida el formato de una campaña sin parsear.
        
        Args:
            campana: String de campaña a validar
            
        Returns:
            True si es válida, False en caso contrario
        """
        try:
            cls.parse_target_year(campana)
            return True
        except CampaignNotFoundError:
            return False