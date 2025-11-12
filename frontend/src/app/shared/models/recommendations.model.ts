export interface SiembraRecommendationRequest {
  lote_id: string;
  cultivo: string;
  campana: string;
  fecha_consulta: string;
  cliente_id: string;
}

export interface RecommendationWindow {
  fecha_optima: string;
  ventana: [string, string];
  confianza: number;
  justificacion?: string;
  riesgos?: string[];
  indicadores_clave?: Record<string, number>;
}

export interface RecommendationAlternative {
  fecha: string;
  ventana: [string, string];
  pros?: string[];
  contras?: string[];
  confianza: number;
  escenario_climatico?: {
    nombre: string;
    descripcion: string;
  };
}

export type CostBreakdown = Record<string, number>;

export interface RecomendacionResponse<TPrincipal = unknown, TAlternative = unknown> {
  lote_id: string;
  tipo_recomendacion: string;
  recomendacion_principal: TPrincipal;
  alternativas: TAlternative[];
  nivel_confianza: number;
  costos_estimados?: CostBreakdown;
  fecha_generacion: string;
  metadata?: Record<string, unknown>;
  datos_entrada?: Record<string, unknown>;
  prediccion_id?: string;
}

export interface SiembraRecommendationResponse extends RecomendacionResponse<RecommendationWindow, RecommendationAlternative> {
  tipo_recomendacion: 'siembra';
  cultivo: string;
}

export interface SiembraHistoryItem {
  id: string;
  lote_id: string;
  cliente_id: string;
  cultivo?: string;
  campana?: string;
  fecha_creacion?: string;
  fecha_validez_desde?: string;
  fecha_validez_hasta?: string;
  nivel_confianza?: number;
  recomendacion_principal: RecommendationWindow;
  alternativas: RecommendationAlternative[];
  modelo_version?: string;
  datos_entrada: Record<string, unknown>;
}

export interface SiembraHistoryResponse {
  total: number;
  items: SiembraHistoryItem[];
}

export interface SiembraHistoryFilters {
  cliente_id?: string;
  lote_id?: string;
  cultivo?: string;
  campana?: string;
}

export interface HealthStatusResponse {
  status?: string;
  environment?: string;
  use_mock_data?: boolean;
  [key: string]: unknown;
}
