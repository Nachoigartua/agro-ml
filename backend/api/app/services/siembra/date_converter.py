"""Conversión entre días del año y fechas."""
from __future__ import annotations

from datetime import datetime, timedelta


class DateConverter:
    """Maneja conversiones entre días del año y fechas."""

    @staticmethod
    def day_of_year_to_date(day_of_year: int, year: int) -> datetime:
        """Convierte día del año a fecha.
        
        Args:
            day_of_year: Día del año (1-365)
            year: Año objetivo
            
        Returns:
            Fecha correspondiente
            
        Raises:
            ValueError: Si day_of_year está fuera de rango
        """
        if not 1 <= day_of_year <= 365:
            raise ValueError(
                f"day_of_year debe estar entre 1 y 365, recibido: {day_of_year}"
            )
        
        start = datetime(year, 1, 1)
        return start + timedelta(days=day_of_year - 1)

    @staticmethod
    def date_to_string(date: datetime, format_str: str = "%d-%m-%Y") -> str:
        """Convierte fecha a string con formato específico.
        
        Args:
            date: Fecha a formatear
            format_str: Formato de salida
            
        Returns:
            Fecha formateada como string
        """
        return date.strftime(format_str)

    @staticmethod
    def create_window(
        center_date: datetime,
        days_before: int = 2,
        days_after: int = 2,
        format_str: str = "%d-%m-%Y"
    ) -> list[str]:
        """Crea una ventana de fechas alrededor de una fecha central.
        
        Args:
            center_date: Fecha central
            days_before: Días antes de la fecha central
            days_after: Días después de la fecha central
            format_str: Formato de salida
            
        Returns:
            Lista con [fecha_inicio, fecha_fin] como strings
        """
        start_date = center_date - timedelta(days=days_before)
        end_date = center_date + timedelta(days=days_after)
        
        return [
            start_date.strftime(format_str),
            end_date.strftime(format_str),
        ]