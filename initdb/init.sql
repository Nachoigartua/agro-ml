CREATE TABLE IF NOT EXISTS modelos_ml (
    id UUID PRIMARY KEY,
    nombre VARCHAR(100),
    version VARCHAR(20),
    tipo_modelo VARCHAR(50),
    archivo_modelo BYTEA,
    metricas_performance JSONB,
    fecha_entrenamiento TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);


CREATE TABLE IF NOT EXISTS predicciones (
    id UUID PRIMARY KEY,
    lote_id UUID NOT NULL,
    cliente_id UUID NOT NULL,
    tipo_prediccion VARCHAR(50) NOT NULL,
    cultivo VARCHAR(50),
    fecha_creacion TIMESTAMP,
    fecha_validez_desde DATE,
    fecha_validez_hasta DATE,
    recomendacion_principal JSONB,
    alternativas JSONB,
    nivel_confianza FLOAT,
    datos_entrada JSONB,
    modelo_version VARCHAR(20)
);
