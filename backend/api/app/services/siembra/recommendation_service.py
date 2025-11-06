"""Servicio orquestador de recomendaciones de siembra."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

import pandas as pd

from ...clients.main_system_client import MainSystemAPIClient
from ...core.logging import get_logger
from ...db.persistence import PersistenceContext
from ...db.models.predicciones import Prediccion
from ...dto.siembra import (
    ALLOWED_CULTIVOS,
    RecomendacionPrincipalSiembra,
    SiembraHistoryItem,
    SiembraRecommendationResponse,
    SiembraRequest,
)
from ...utils.validators import validate_cultivo

from .model_loader import ModelLoader
from .feature_builder import FeatureBuilder
from .predictor import SiembraPredictor
from .date_converter import DateConverter
from .campaign_parser import CampaignParser
from .alternative_generator import AlternativeGenerator
from .risk_analyzer import SiembraRiskAnalyzer
from ..confidence_service import ConfidenceService


logger = get_logger("siembra.recommendation_service")


class SiembraRecommendationService:
    """Servicio principal para generar recomendaciones de siembra.

    Orquesta las diferentes responsabilidades delegando a componentes especializados.
    Integra análisis de riesgo climático usando datos históricos.
    """

    def __init__(
        self,
        main_system_client: MainSystemAPIClient,
        *,
        persistence_context: PersistenceContext,
        model_name: str = "modelo_siembra",
        model_type: str = "random_forest_regressor",
        risk_analyzer: Optional[SiembraRiskAnalyzer] = None,
    ) -> None:
        """Inicializa el servicio de recomendaciones.

        Args:
            main_system_client: Cliente para obtener datos del sistema principal
            persistence_context: Contexto de persistencia
            model_name: Nombre del modelo a usar
            model_type: Tipo de modelo
            risk_analyzer: Analizador de riesgos climáticos (opcional)
        """
        self.main_system_client = main_system_client
        self._persistence_context = persistence_context

        # Componentes especializados
        self._model_loader = ModelLoader(
            persistence_context=persistence_context,
            model_name=model_name,
            model_type=model_type,
        )
        self._feature_builder: Optional[FeatureBuilder] = None
        self._predictor: Optional[SiembraPredictor] = None
        self._date_converter = DateConverter()
        self._campaign_parser = CampaignParser()
        self._alternative_generator: Optional[AlternativeGenerator] = None

        # Servicio de confianza basado en métricas del modelo
        self._confidence_service = ConfidenceService()
        self._model_performance_metrics: Dict[str, Any] = {}

        # Analizador de riesgos climáticos
        self._risk_analyzer = risk_analyzer or SiembraRiskAnalyzer(logger=logger)

    async def generate_recommendation(
        self,
        request: SiembraRequest,
    ) -> SiembraRecommendationResponse:
        """Genera una recomendación de siembra con análisis de riesgo.
        
        Args:
            request: Solicitud con datos del lote y cultivo
            
        Returns:
            Recomendación de siembra con fecha óptima, ventana, alternativa y riesgos
            
        Raises:
            ValueError: Si los datos del lote son inválidos
            CampaignNotFoundError: Si la campaña es inválida
        """
        await self._ensure_components_ready()

        # 1. Obtener datos del lote
        lote_data = await self.main_system_client.get_lote_data(request.lote_id)
        if not lote_data:
            raise ValueError(f"No se encontraron datos para el lote {request.lote_id}")

        # 2. Construir features
        feature_row = self._feature_builder.build(
            lote_data=lote_data,
            cultivo_override=request.cultivo
        )

        # 3. Predecir día del año
        dataframe = pd.DataFrame(
            [feature_row],
            columns=self._model_loader.feature_order
        )
        predicted_day = self._predictor.predict_day_of_year(dataframe)

        # 4. Convertir a fecha
        target_year = self._campaign_parser.parse_target_year(request.campana)
        fecha_optima = self._date_converter.day_of_year_to_date(predicted_day, target_year)

        # 5. Calcular nivel de confianza basado en métricas del modelo cargado
        confianza = self._confidence_service.score(self._model_performance_metrics)

        # 6. Crear ventana de siembra
        ventana = self._date_converter.create_window(fecha_optima)
        ventana_inicio = fecha_optima - timedelta(days=2)
        ventana_fin = fecha_optima + timedelta(days=2)

        # 7. Análisis de riesgos climáticos
        try:
            riesgos = await self._risk_analyzer.evaluate(
                lote_data,
                fecha_objetivo=fecha_optima,
                ventana=(ventana_inicio, ventana_fin),
            )
            logger.info(
                "Análisis de riesgos completado",
                extra={
                    "lote_id": request.lote_id,
                    "num_riesgos": len(riesgos),
                }
            )
        except Exception:
            logger.exception(
                "Error durante el análisis de riesgos de siembra",
                extra={"lote_id": request.lote_id}
            )
            riesgos = [self._risk_analyzer.default_risk_message]

        # 8. Construir recomendación principal con riesgos
        recomendacion_principal = RecomendacionPrincipalSiembra(
            fecha_optima=self._date_converter.date_to_string(fecha_optima),
            ventana=ventana,
            confianza=confianza,
            riesgos=riesgos,  
        )

        # 9. Generar alternativa con escenario climático
        alternativa = self._alternative_generator.generate(feature_row, target_year, confianza)

        # 10. Construir respuesta
        response = SiembraRecommendationResponse(
            lote_id=request.lote_id,
            tipo_recomendacion="siembra",
            recomendacion_principal=recomendacion_principal,
            alternativas=[alternativa],
            nivel_confianza=confianza,
            factores_considerados=[],  # TODO: Implementar factores
            costos_estimados={},  # TODO: Implementar costos
            fecha_generacion=datetime.now(timezone.utc),
            cultivo=request.cultivo,
            datos_entrada=request.model_dump(mode="json"),
        )

        # 11. Persistir recomendación
        await self._persist_recommendation(request, response)

        logger.info(
            "Recomendación de siembra generada exitosamente",
            extra={
                "lote_id": request.lote_id,
                "cultivo": request.cultivo,
                "fecha_optima": recomendacion_principal.fecha_optima,
                "alternativa_escenario": alternativa.get("escenario_climatico", {}).get("nombre"),
                "tiene_riesgos": len(riesgos) > 0,
            }
        )

        return response

    async def get_history(
        self,
        *,
        cliente_id: Optional[str] = None,
        lote_id: Optional[str] = None,
        cultivo: Optional[str] = None,
        campana: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SiembraHistoryItem]:
        """Recupera el historial de recomendaciones de siembra.

        Args:
            cliente_id: Filtrar por cliente
            lote_id: Filtrar por lote
            cultivo: Filtrar por cultivo
            campana: Filtrar por campaña
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de recomendaciones históricas

        Raises:
            RuntimeError: Si no hay repositorio configurado
            ValueError: Si cultivo es inválido
        """
        if self._persistence_context.predicciones is None:
            raise RuntimeError(
                "El contexto de persistencia no cuenta con repositorio de predicciones."
            )

        # Validar y normalizar cultivo si se proporciona
        normalised_cultivo: Optional[str] = None
        if cultivo is not None:
            normalised_cultivo = validate_cultivo(cultivo, ALLOWED_CULTIVOS)

        # Obtener registros
        registros = await self._persistence_context.predicciones.list_by_filters(
            tipo_prediccion="siembra",
            cliente_id=cliente_id,
            lote_id=lote_id,
            cultivo=normalised_cultivo,
            campana=campana,
            limit=limit,
            offset=offset,
        )

        return [self._map_prediccion_to_history_item(pred) for pred in registros]

    async def _ensure_components_ready(self) -> None:
        """Asegura que todos los componentes estén listos para uso."""
        # Cargar modelo si no está cargado
        await self._model_loader.load()

        # Tomar métricas de performance del loader para cálculo de confianza
        try:
            self._model_performance_metrics = dict(self._model_loader.performance_metrics)
        except Exception:  # pragma: no cover
            self._model_performance_metrics = {}

        # Inicializar componentes que dependen del modelo
        if self._feature_builder is None:
            defaults = self._model_loader.feature_defaults
            self._feature_builder = FeatureBuilder(
                feature_order=self._model_loader.feature_order,
                numeric_defaults={
                    k: float(v) for k, v in defaults.get("numeric", {}).items()
                },
                categorical_defaults={
                    k: str(v) for k, v in defaults.get("categorical", {}).items()
                },
            )

        if self._predictor is None:
            self._predictor = SiembraPredictor(
                model=self._model_loader.model,
                preprocessor=self._model_loader.preprocessor,
            )

        if self._alternative_generator is None:
            self._alternative_generator = AlternativeGenerator(
                predictor=self._predictor,
                feature_order=self._model_loader.feature_order,
                date_converter=self._date_converter,
            )

    async def _persist_recommendation(
        self,
        request: SiembraRequest,
        response: SiembraRecommendationResponse,
    ) -> None:
        """Persiste la recomendación generada.

        Args:
            request: Request original
            response: Respuesta generada
            
        Raises:
            RuntimeError: Si no hay repositorio configurado
        """
        if self._persistence_context.predicciones is None:
            raise RuntimeError(
                "El contexto de persistencia no cuenta con repositorio de predicciones."
            )

        # Parsear ventana a fechas
        ventana = response.recomendacion_principal.ventana
        fecha_validez_desde = None
        fecha_validez_hasta = None

        if len(ventana) == 2:
            try:
                fecha_validez_desde = datetime.strptime(ventana[0], "%d-%m-%Y").date()
                fecha_validez_hasta = datetime.strptime(ventana[1], "%d-%m-%Y").date()
            except ValueError:
                logger.warning(
                    "No se pudo parsear la ventana a fechas válidas",
                    extra={"ventana": ventana}
                )

        # Guardar en base de datos
        await self._persistence_context.predicciones.save(
            lote_id=request.lote_id,
            cliente_id=request.cliente_id,
            tipo_prediccion=response.tipo_recomendacion,
            cultivo=response.cultivo,
            recomendacion_principal=response.recomendacion_principal.model_dump(mode="json"),
            alternativas=[dict(alt) for alt in response.alternativas],
            nivel_confianza=response.nivel_confianza,
            datos_entrada=request.model_dump(mode="json"),
            modelo_version=self._model_loader.metadata.get("version"),
            fecha_validez_desde=fecha_validez_desde,
            fecha_validez_hasta=fecha_validez_hasta,
        )

    def _map_prediccion_to_history_item(self, entidad: Prediccion) -> SiembraHistoryItem:
        """Convierte entidad ORM a DTO de historial.

        Args:
            entidad: Entidad de predicción
            
        Returns:
            Item de historial
            
        Raises:
            ValueError: Si los datos persistidos son corruptos
        """
        principal_data = entidad.recomendacion_principal or {}

        try:
            recomendacion_principal = RecomendacionPrincipalSiembra(**principal_data)
        except Exception as exc:
            raise ValueError(
                "Los datos persistidos de la recomendación principal son inválidos"
            ) from exc

        alternativas_raw = entidad.alternativas or []
        alternativas = [
            dict(alt) if isinstance(alt, dict) else alt
            for alt in alternativas_raw
        ]

        datos_entrada = dict(entidad.datos_entrada or {})

        return SiembraHistoryItem(
            id=entidad.id,
            lote_id=entidad.lote_id,
            cliente_id=entidad.cliente_id,
            cultivo=entidad.cultivo,
            campana=datos_entrada.get("campana"),
            fecha_creacion=entidad.fecha_creacion,
            fecha_validez_desde=entidad.fecha_validez_desde,
            fecha_validez_hasta=entidad.fecha_validez_hasta,
            nivel_confianza=entidad.nivel_confianza,
            recomendacion_principal=recomendacion_principal,
            alternativas=alternativas,
            modelo_version=entidad.modelo_version,
            datos_entrada=datos_entrada,
        )
