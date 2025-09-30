-- Agro ML Database Schema
-- PostgreSQL con PostGIS

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de predicciones
CREATE TABLE IF NOT EXISTS predicciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lote_id VARCHAR(100),
    cliente_id VARCHAR(100),
    tipo_prediccion VARCHAR(50) NOT NULL,
    cultivo VARCHAR(50),
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_validez_desde DATE,
    fecha_validez_hasta DATE,
    recomendacion_principal JSONB NOT NULL,
    alternativas JSONB DEFAULT '[]'::jsonb,
    nivel_confianza FLOAT CHECK (nivel_confianza >= 0 AND nivel_confianza <= 1),
    datos_entrada JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para predicciones
CREATE INDEX IF NOT EXISTS idx_predicciones_lote_id ON predicciones(lote_id);
CREATE INDEX IF NOT EXISTS idx_predicciones_cliente_id ON predicciones(cliente_id);
CREATE INDEX IF NOT EXISTS idx_predicciones_tipo ON predicciones(tipo_prediccion);
CREATE INDEX IF NOT EXISTS idx_predicciones_cultivo ON predicciones(cultivo);
CREATE INDEX IF NOT EXISTS idx_predicciones_fecha ON predicciones(fecha_creacion DESC);

-- Tabla de datos climáticos históricos
CREATE TABLE IF NOT EXISTS clima_historico (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    latitud FLOAT NOT NULL,
    longitud FLOAT NOT NULL,
    fecha DATE NOT NULL,
    temperatura_max FLOAT,
    temperatura_min FLOAT,
    temperatura_media FLOAT,
    precipitacion FLOAT,
    humedad_relativa FLOAT,
    radiacion_solar FLOAT,
    velocidad_viento FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(latitud, longitud, fecha)
);

-- Índices para clima
CREATE INDEX IF NOT EXISTS idx_clima_coords_fecha ON clima_historico(latitud, longitud, fecha DESC);
CREATE INDEX IF NOT EXISTS idx_clima_fecha ON clima_historico(fecha DESC);

-- Tabla de características de suelo
CREATE TABLE IF NOT EXISTS caracteristicas_suelo (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lote_id VARCHAR(100) NOT NULL,
    profundidad_cm INTEGER,
    ph FLOAT,
    materia_organica FLOAT,
    nitrogeno FLOAT,
    fosforo FLOAT,
    potasio FLOAT,
    textura VARCHAR(50),
    capacidad_campo FLOAT,
    conductividad_electrica FLOAT,
    fecha_analisis TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para suelo
CREATE INDEX IF NOT EXISTS idx_suelo_lote ON caracteristicas_suelo(lote_id);
CREATE INDEX IF NOT EXISTS idx_suelo_fecha ON caracteristicas_suelo(fecha_analisis DESC);

-- Tabla de modelos ML (metadata)
CREATE TABLE IF NOT EXISTS modelos_ml (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    tipo_modelo VARCHAR(50),
    metricas_performance JSONB,
    fecha_entrenamiento TIMESTAMP NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(nombre, version)
);

-- Índices para modelos
CREATE INDEX IF NOT EXISTS idx_modelos_nombre ON modelos_ml(nombre);
CREATE INDEX IF NOT EXISTS idx_modelos_activo ON modelos_ml(activo);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_predicciones_updated_at BEFORE UPDATE ON predicciones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_suelo_updated_at BEFORE UPDATE ON caracteristicas_suelo
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertar datos de ejemplo (opcional)
-- Se pueden descomentar para tener datos iniciales

/*
INSERT INTO caracteristicas_suelo (
    lote_id, ph, materia_organica, nitrogeno, fosforo, potasio, 
    textura, fecha_analisis
) VALUES
    ('lote-001', 6.5, 3.2, 22.0, 15.0, 220.0, 'franco', NOW() - INTERVAL '30 days'),
    ('lote-002', 6.8, 2.9, 18.0, 12.0, 195.0, 'arcilloso', NOW() - INTERVAL '45 days'),
    ('lote-003', 7.0, 3.5, 25.0, 18.0, 240.0, 'franco', NOW() - INTERVAL '20 days');
*/

-- View para estadísticas de predicciones
CREATE OR REPLACE VIEW predicciones_stats AS
SELECT 
    tipo_prediccion,
    cultivo,
    COUNT(*) as total_predicciones,
    AVG(nivel_confianza) as confianza_promedio,
    DATE_TRUNC('month', fecha_creacion) as mes
FROM predicciones
GROUP BY tipo_prediccion, cultivo, DATE_TRUNC('month', fecha_creacion)
ORDER BY mes DESC;

-- Comentarios en las tablas
COMMENT ON TABLE predicciones IS 'Almacena todas las predicciones generadas por los modelos ML';
COMMENT ON TABLE clima_historico IS 'Datos climáticos históricos por ubicación';
COMMENT ON TABLE caracteristicas_suelo IS 'Características del suelo por lote';
COMMENT ON TABLE modelos_ml IS 'Metadata de los modelos de machine learning';

-- Grant permissions (ajustar según necesidades)
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO agro_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO agro_user;