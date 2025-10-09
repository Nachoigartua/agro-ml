export interface SiembraRecommendationRequest {
  lote_id: string;
  cultivo: string;
  campana: string;
  fecha_consulta: string;
  cliente_id: string; // provisto por el FE (por ahora fijo)
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
  pros?: string[];
  contras?: string[];
  confianza: number;
}

export type CostBreakdown = Record<string, number>;

export interface RecomendacionResponse<TPrincipal = unknown, TAlternative = unknown> {
  lote_id: string;
  tipo_recomendacion: string;
  recomendacion_principal: TPrincipal;
  alternativas: TAlternative[];
  nivel_confianza: number;
  factores_considerados: string[];
  costos_estimados?: CostBreakdown;
  fecha_generacion: string;
  metadata?: Record<string, unknown>;
}

export interface SiembraRecommendationResponse extends RecomendacionResponse<RecommendationWindow, RecommendationAlternative> {
  tipo_recomendacion: 'siembra';
  cultivo: string;
}

export interface HealthStatusResponse {
  status?: string;
  environment?: string;
  use_mock_data?: boolean;
  [key: string]: unknown;
}
