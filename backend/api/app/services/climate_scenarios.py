"""Módulo de escenarios climáticos para alternativas de siembra."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ClimateScenario:
    """Representa un escenario climático extremo para generar alternativas."""
    
    nombre: str
    descripcion: str
    precip_factor: float
    temp_adjustment: float


class ClimateScenarioGenerator:
    """Generador de escenarios climáticos y análisis de pros/contras."""
    
    # Definición de escenarios climáticos extremos pero realistas
    SCENARIOS = [
        {
            'nombre': 'Sequía severa',
            'descripcion': 'Escenario con precipitaciones 50% por debajo del promedio y temperaturas 4°C más altas',
            'precip_range': (0.45, 0.55),  # 45-55% del promedio
            'temp_range': (3.5, 4.5),  # +3.5 a +4.5°C
        },
        {
            'nombre': 'Año húmedo extremo',
            'descripcion': 'Escenario con precipitaciones 60% por encima del promedio y temperaturas 2°C más bajas',
            'precip_range': (1.55, 1.65),  # 155-165% del promedio
            'temp_range': (-2.5, -1.5),  # -2.5 a -1.5°C
        },
        {
            'nombre': 'Riesgo de heladas tardías',
            'descripcion': 'Escenario con temperaturas 5°C por debajo del promedio en periodo crítico',
            'precip_range': (0.90, 1.10),  # Precipitaciones normales
            'temp_range': (-5.5, -4.5),  # -5.5 a -4.5°C
        },
        {
            'nombre': 'Ola de calor temprana',
            'descripcion': 'Escenario con temperaturas 6°C por encima del promedio y baja humedad',
            'precip_range': (0.60, 0.75),  # 60-75% del promedio
            'temp_range': (5.0, 6.5),  # +5 a +6.5°C
        },
        {
            'nombre': 'Año Niña moderado',
            'descripcion': 'Escenario típico de año La Niña con precipitaciones reducidas y temperaturas elevadas',
            'precip_range': (0.65, 0.80),  # 65-80% del promedio
            'temp_range': (2.0, 3.5),  # +2 a +3.5°C
        },
        {
            'nombre': 'Primavera inestable',
            'descripcion': 'Escenario con alta variabilidad: precipitaciones excesivas y temperaturas erráticas',
            'precip_range': (1.30, 1.50),  # 130-150% del promedio
            'temp_range': (-1.5, 1.5),  # Temperatura variable
        },
    ]
    
    # Mapeo de escenarios a pros y contras
    SCENARIO_ANALYSIS = {
        'Sequía severa': {
            'pros': [
                "Menor riesgo de anegamiento",
                "Reducción de enfermedades fúngicas",
            ],
            'contras': [
                "Severo estrés hídrico durante ciclo",
                "Germinación comprometida",
                "Rendimientos significativamente reducidos",
            ],
        },
        'Año húmedo extremo': {
            'pros': [
                "Excelente disponibilidad hídrica",
                "Sin limitaciones por agua durante ciclo",
            ],
            'contras': [
                "Alto riesgo de enfermedades fúngicas",
                "Posible anegamiento en lotes bajos",
                "Dificultades en labores de campo",
            ],
        },
        'Riesgo de heladas tardías': {
            'pros': [
                "Buena humedad en suelo",
                "Menor evapotranspiración",
            ],
            'contras': [
                "Alto riesgo de daño por heladas",
                "Desarrollo inicial muy lento",
                "Posible pérdida total del cultivo",
            ],
        },
        'Ola de calor temprana': {
            'pros': [
                "Germinación muy rápida",
                "Desarrollo inicial acelerado",
            ],
            'contras': [
                "Severo estrés térmico e hídrico",
                "Agotamiento rápido de humedad",
                "Acortamiento significativo del ciclo",
            ],
        },
        'Año Niña moderado': {
            'pros': [
                "Menor riesgo de anegamiento",
                "Germinación más rápida",
            ],
            'contras': [
                "Disponibilidad hídrica limitada",
                "Mayor estrés durante floración",
            ],
        },
        'Primavera inestable': {
            'pros': [
                "Buena recarga de humedad",
                "Temperaturas moderadas",
            ],
            'contras': [
                "Alta variabilidad climática",
                "Dificultad en planificación de labores",
                "Riesgo de enfermedades por humedad",
            ],
        },
    }
    
    @classmethod
    def get_random_scenario(cls) -> ClimateScenario:
        """Selecciona y genera un escenario climático aleatorio.
        
        Returns:
            Escenario climático con valores aleatorios dentro de rangos definidos
        """
        scenario_def = random.choice(cls.SCENARIOS)
        
        precip_min, precip_max = scenario_def['precip_range']
        temp_min, temp_max = scenario_def['temp_range']
        
        return ClimateScenario(
            nombre=scenario_def['nombre'],
            descripcion=scenario_def['descripcion'],
            precip_factor=random.uniform(precip_min, precip_max),
            temp_adjustment=random.uniform(temp_min, temp_max),
        )
    
    @classmethod
    def get_pros_contras(cls, scenario_name: str) -> Tuple[List[str], List[str]]:
        """Obtiene los pros y contras para un escenario específico.
        
        Args:
            scenario_name: Nombre del escenario climático
            
        Returns:
            Tupla con (pros, contras)
        """
        analysis = cls.SCENARIO_ANALYSIS.get(scenario_name, {})
        pros = analysis.get('pros', [])
        contras = analysis.get('contras', [])
        return pros, contras
    
    @classmethod
    def apply_scenario_to_features(
        cls,
        feature_row: Dict[str, Any],
        scenario: ClimateScenario,
    ) -> Dict[str, Any]:
        """Aplica las modificaciones del escenario a las features climáticas.
        
        Args:
            feature_row: Diccionario con las features originales
            scenario: Escenario climático a aplicar
            
        Returns:
            Diccionario con las features modificadas (copia del original)
        """
        modified_row = feature_row.copy()
        
        # Lista de features climáticas a modificar
        precip_features = ["precipitacion_marzo", "precipitacion_abril", "precipitacion_mayo"]
        temp_features = ["temp_media_marzo", "temp_media_abril", "temp_media_mayo"]
        
        # Aplicar factor de precipitación
        for precip_key in precip_features:
            if precip_key in modified_row and modified_row[precip_key] is not None:
                modified_row[precip_key] = modified_row[precip_key] * scenario.precip_factor
        
        # Aplicar ajuste de temperatura
        for temp_key in temp_features:
            if temp_key in modified_row and modified_row[temp_key] is not None:
                modified_row[temp_key] = modified_row[temp_key] + scenario.temp_adjustment
        
        return modified_row