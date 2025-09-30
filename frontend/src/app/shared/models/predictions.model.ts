export interface PredictionRequest {
  lote_id: string;
  cliente_id: string;
  cultivo: string;
  [key: string]: any;
}

export interface PredictionResponse {
  lote_id?: string;
  tipo_prediccion: string;
  recomendacion_principal: any;
  alternativas: any[];
  nivel_confianza: number;
  factores_considerados: string[];
  fecha_generacion: string;
  metadata?: any;
}

export interface SiembraRequest extends PredictionRequest {
  campana: string;
}

export interface VariedadRequest extends PredictionRequest {
  objetivo_productivo?: string;
}

export interface RendimientoRequest extends PredictionRequest {
  fecha_siembra: string;
  variedad?: string;
}

export interface FertilizacionRequest extends PredictionRequest {
  objetivo_rendimiento?: number;
}

export interface ClimaRequest {
  latitud: number;
  longitud: number;
  fecha_desde: string;
  fecha_hasta: string;
}

export interface CosechaRequest extends PredictionRequest {
  fecha_siembra: string;
  variedad?: string;
}

export interface Lote {
  id: string;
  cliente_id: string;
  nombre: string;
  latitud: number;
  longitud: number;
  superficie_ha: number;
  tipo_suelo: string;
  caracteristicas?: any;
}

export interface ModelStatus {
  name: string;
  loaded: boolean;
  metadata: {
    trained_at?: string;
    version?: string;
    metrics?: any;
  };
  path: string;
}