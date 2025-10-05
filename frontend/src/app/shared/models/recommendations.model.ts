export interface Lote {
  id: string;
  cliente_id: string;
  nombre: string;
  latitud: number;
  longitud: number;
  superficie_ha: number;
  tipo_suelo: string;
  caracteristicas?: Record<string, unknown>;
}

export interface SiembraRecommendationRequest {
  lote_id: string;
  cliente_id: string;
  cultivo: string;
  campana: string;
  fecha_consulta: string;
}

export interface RecommendationWindow {
  fecha_optima: string;
  ventana: [string, string];
  confianza: number;
  justificacion?: string;
  riesgos?: string[];
  indicadores_clave?: Record<string, number>;
}

export type RecommendationAlternative = RecommendationWindow & {
  etiqueta?: string;
};

export type CostBreakdown = Record<string, number>;

export interface SiembraRecommendationResponse {
  lote_id: string;
  tipo_recomendacion: 'siembra';
  recomendacion_principal: RecommendationWindow;
  alternativas: RecommendationAlternative[];
  nivel_confianza: number;
  factores_considerados: string[];
  costos_estimados?: CostBreakdown;
  fecha_generacion: string;
  metadata?: Record<string, unknown>;
}

export interface ModelStatus {
  name: string;
  loaded: boolean;
  metadata: {
    trained_at?: string;
    version?: string;
    metrics?: Record<string, number>;
  };
  path: string;
}

export interface HealthStatusResponse {
  status?: string;
  environment?: string;
  use_mock_data?: boolean;
  [key: string]: unknown;
}

export interface ModelsDashboardState {
  cache_connected?: boolean;
  models?: Record<string, ModelStatus>;
  [key: string]: unknown;
}
