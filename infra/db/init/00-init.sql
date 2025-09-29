-- Schema init for AgroML demo (no hardcoded responses; data lives in DB)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS lotes (
    id UUID PRIMARY KEY,
    nombre TEXT NOT NULL,
    latitud DOUBLE PRECISION NOT NULL,
    longitud DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS caracteristicas_suelo (
    id SERIAL PRIMARY KEY,
    lote_id UUID REFERENCES lotes(id) ON DELETE CASCADE,
    materia_organica DOUBLE PRECISION NOT NULL,
    ph DOUBLE PRECISION NOT NULL,
    cec DOUBLE PRECISION NOT NULL,
    fecha TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS clima_historico (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    latitud DOUBLE PRECISION NOT NULL,
    longitud DOUBLE PRECISION NOT NULL,
    temperatura_max DOUBLE PRECISION NOT NULL,
    temperatura_min DOUBLE PRECISION NOT NULL,
    precipitacion DOUBLE PRECISION NOT NULL,
    humedad_relativa DOUBLE PRECISION NOT NULL,
    velocidad_viento DOUBLE PRECISION NOT NULL,
    radiacion_solar DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS cultivos(
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS campanas(
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS variedades_catalogo(
    id SERIAL PRIMARY KEY,
    cultivo TEXT NOT NULL,
    variedad TEXT NOT NULL,
    madurez TEXT NOT NULL,
    rendimiento_base_kg_ha DOUBLE PRECISION NOT NULL,
    tolerancias JSONB,
    justificacion TEXT
);

-- Seed base catalog data (idempotent)
INSERT INTO cultivos(nombre) VALUES ('Maiz') ON CONFLICT DO NOTHING;
INSERT INTO cultivos(nombre) VALUES ('Soja') ON CONFLICT DO NOTHING;
INSERT INTO cultivos(nombre) VALUES ('Trigo') ON CONFLICT DO NOTHING;

INSERT INTO campanas(nombre) VALUES ('2024/25') ON CONFLICT DO NOTHING;
INSERT INTO campanas(nombre) VALUES ('2025/26') ON CONFLICT DO NOTHING;

-- Lotes with stable UUIDs (match UI demo)
INSERT INTO lotes(id, nombre, latitud, longitud) VALUES
    ('79f666dc-8b9b-4119-b7ec-dcf1beda53b1','Lote Norte', -34.600, -58.400)
ON CONFLICT (id) DO NOTHING;

INSERT INTO lotes(id, nombre, latitud, longitud) VALUES
    ('7bab8213-c0d8-4787-b588-41123834a886','Lote Sur', -33.100, -60.600)
ON CONFLICT (id) DO NOTHING;

INSERT INTO lotes(id, nombre, latitud, longitud) VALUES
    ('3a7a4a66-6d2e-4c8e-9c3f-9b8f2d3b4a55','Lote Este', -32.950, -60.650)
ON CONFLICT (id) DO NOTHING;

-- Soil characteristics (latest row used)
INSERT INTO caracteristicas_suelo(lote_id, materia_organica, ph, cec, fecha) VALUES
('79f666dc-8b9b-4119-b7ec-dcf1beda53b1', 3.2, 6.4, 18.0, NOW() - INTERVAL '3 days'),
('7bab8213-c0d8-4787-b588-41123834a886', 2.8, 6.0, 15.0, NOW() - INTERVAL '2 days'),
('3a7a4a66-6d2e-4c8e-9c3f-9b8f2d3b4a55', 3.5, 6.5, 20.0, NOW() - INTERVAL '1 days');

-- Varieties
INSERT INTO variedades_catalogo(cultivo, variedad, madurez, rendimiento_base_kg_ha, tolerancias, justificacion) VALUES
('Maiz','MX-745','Intermedia', 9000, '{"estrés_hídrico":"media","frío":"alta"}',
 'Buen comportamiento en siembras tempranas y suelos francos'),
('Maiz','MX-820','Intermedia-tardía', 9500, '{"estrés_hídrico":"alta","frío":"media"}',
 'Alto potencial con buena estabilidad'),
('Maiz','MX-620','Temprana', 8800, '{"estrés_hídrico":"media","frío":"media"}',
 'Se adapta a fechas de siembra ajustadas'),
('Soja','SJ-5.0','Grupo V', 3400, '{"enfermedades":"resistente"}',
 'Buen comportamiento sanitario'),
('Soja','SJ-4.8','Grupo IV largo', 3300, '{"estrés_hídrico":"media"}',
 'Estabilidad en ambientes medios'),
('Trigo','TR-118','Ciclo intermedio', 4700, '{"heladas":"tolerante"}',
 'Buen peso hectolítrico');

-- Simple climate generator for last 10 days in 2 coords
DO $$
DECLARE
    d DATE;
BEGIN
  FOR d IN (SELECT CURRENT_DATE - offs AS f FROM generate_series(0,9) AS offs) LOOP
    -- BA coordinates
    INSERT INTO clima_historico(fecha, latitud, longitud, temperatura_max, temperatura_min, precipitacion, humedad_relativa, velocidad_viento, radiacion_solar)
    VALUES (d, -34.600, -58.400,
            26 + random()*4, 14 + random()*3, 2.0 + random()*3, 55 + random()*15, 12 + random()*3, 18 + random()*4);
    -- Sur coordinates
    INSERT INTO clima_historico(fecha, latitud, longitud, temperatura_max, temperatura_min, precipitacion, humedad_relativa, velocidad_viento, radiacion_solar)
    VALUES (d, -33.100, -60.600,
            25 + random()*4, 12 + random()*3, 1.5 + random()*3, 60 + random()*10, 10 + random()*3, 17 + random()*4);
    -- Este coordinates
    INSERT INTO clima_historico(fecha, latitud, longitud, temperatura_max, temperatura_min, precipitacion, humedad_relativa, velocidad_viento, radiacion_solar)
    VALUES (d, -32.950, -60.650,
            27 + random()*3, 15 + random()*2, 1.0 + random()*2, 58 + random()*10, 9 + random()*3, 19 + random()*3);
  END LOOP;
END $$;
