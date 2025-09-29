-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Catalog tables
CREATE TABLE IF NOT EXISTS campanas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cultivos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre TEXT NOT NULL,
  tipo TEXT
);

CREATE TABLE IF NOT EXISTS lotes (
  id UUID PRIMARY KEY,
  nombre TEXT NOT NULL,
  latitud DOUBLE PRECISION NOT NULL,
  longitud DOUBLE PRECISION NOT NULL,
  hectareas DOUBLE PRECISION NOT NULL,
  cultivo_id UUID NULL REFERENCES cultivos(id)
);

-- Weather
CREATE TABLE IF NOT EXISTS clima_historico (
  id BIGSERIAL PRIMARY KEY,
  latitud DOUBLE PRECISION NOT NULL,
  longitud DOUBLE PRECISION NOT NULL,
  fecha DATE NOT NULL,
  temperatura_max DOUBLE PRECISION NOT NULL,
  temperatura_min DOUBLE PRECISION NOT NULL,
  precipitacion DOUBLE PRECISION NOT NULL,
  humedad_relativa DOUBLE PRECISION NOT NULL,
  velocidad_viento DOUBLE PRECISION NOT NULL,
  radiacion_solar DOUBLE PRECISION NOT NULL
);

-- Soil
CREATE TABLE IF NOT EXISTS mediciones_suelo (
  id BIGSERIAL PRIMARY KEY,
  lote_id UUID NOT NULL,
  fecha DATE NOT NULL DEFAULT CURRENT_DATE,
  materia_organica DOUBLE PRECISION NOT NULL,
  ph DOUBLE PRECISION,
  textura TEXT
);

-- Yields
CREATE TABLE IF NOT EXISTS rendimientos (
  id BIGSERIAL PRIMARY KEY,
  lote_id UUID NOT NULL,
  anio INT NOT NULL,
  rendimiento_kg_ha INT NOT NULL
);

-- Seed data (idempotent)
INSERT INTO campanas (id, nombre) VALUES
  (gen_random_uuid(), 'Campaña 2024/25'),
  (gen_random_uuid(), 'Campaña 2023/24')
ON CONFLICT DO NOTHING;

INSERT INTO cultivos (id, nombre, tipo) VALUES
  (gen_random_uuid(), 'Maíz', 'Grano'),
  (gen_random_uuid(), 'Soja', 'Grano')
ON CONFLICT DO NOTHING;

INSERT INTO lotes (id, nombre, latitud, longitud, hectareas)
VALUES
  ('79f666dc-8b9b-4119-b7ec-dcf1beda53b1', 'Lote Norte', -34.6, -58.4, 75),
  ('7bab8213-c0d8-4787-b588-41123834a886', 'Lote Sur',   -33.1, -60.6, 120),
  ('11111111-2222-3333-4444-555555555555', 'Lote Este',  -34.9, -58.0, 50)
ON CONFLICT (id) DO NOTHING;

-- Soil MO
INSERT INTO mediciones_suelo (lote_id, fecha, materia_organica, ph, textura) VALUES
  ('79f666dc-8b9b-4119-b7ec-dcf1beda53b1', CURRENT_DATE - INTERVAL '30 days', 2.5, 6.2, 'Franca'),
  ('79f666dc-8b9b-4119-b7ec-dcf1beda53b1', CURRENT_DATE - INTERVAL '5 days',  2.8, 6.1, 'Franca'),
  ('7bab8213-c0d8-4787-b588-41123834a886', CURRENT_DATE - INTERVAL '10 days', 3.4, 6.5, 'Franco-arenosa'),
  ('11111111-2222-3333-4444-555555555555', CURRENT_DATE - INTERVAL '15 days', 1.9, 5.9, 'Arcillosa')
ON CONFLICT DO NOTHING;

-- Yields
INSERT INTO rendimientos (lote_id, anio, rendimiento_kg_ha) VALUES
  ('79f666dc-8b9b-4119-b7ec-dcf1beda53b1', 2023, 7200), ('79f666dc-8b9b-4119-b7ec-dcf1beda53b1', 2022, 6900), ('79f666dc-8b9b-4119-b7ec-dcf1beda53b1', 2021, 6500),
  ('7bab8213-c0d8-4787-b588-41123834a886', 2023, 8000), ('7bab8213-c0d8-4787-b588-41123834a886', 2022, 7700), ('7bab8213-c0d8-4787-b588-41123834a886', 2021, 7900),
  ('11111111-2222-3333-4444-555555555555', 2023, 6200), ('11111111-2222-3333-4444-555555555555', 2022, 6100), ('11111111-2222-3333-4444-555555555555', 2021, 6000)
ON CONFLICT DO NOTHING;

-- Weather data for three ubicaciones (10 días)
INSERT INTO clima_historico (latitud, longitud, fecha, temperatura_max, temperatura_min, precipitacion, humedad_relativa, velocidad_viento, radiacion_solar)
VALUES
  -- -34.6, -58.4
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '0 day', 30, 16, 4.5, 70, 14, 20),
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '1 day', 29, 15, 2.0, 64, 12, 18),
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '2 day', 28, 14, 0.0, 55, 10, 16),
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '3 day', 31, 17, 1.5, 62, 18, 22),
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '4 day', 27, 13, 6.0, 75, 20, 19),
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '5 day', 26, 12, 9.0, 82, 9,  15),
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '6 day', 32, 17, 3.5, 66, 14, 23),
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '7 day', 30, 16, 2.0, 60, 15, 21),
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '8 day', 29, 15, 0.0, 58, 12, 18),
  (-34.6, -58.4, CURRENT_DATE - INTERVAL '9 day', 28, 14, 1.0, 61, 11, 17),

  -- -33.1, -60.6
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '0 day', 31, 17, 5.0, 72, 16, 21),
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '1 day', 30, 16, 1.0, 63, 14, 19),
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '2 day', 27, 13, 0.0, 54, 9,  16),
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '3 day', 32, 18, 2.5, 65, 20, 23),
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '4 day', 26, 12, 7.0, 78, 18, 18),
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '5 day', 25, 11, 8.5, 80, 10, 14),
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '6 day', 30, 16, 4.0, 68, 13, 22),
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '7 day', 29, 15, 2.5, 63, 16, 20),
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '8 day', 28, 14, 1.0, 60, 12, 18),
  (-33.1, -60.6, CURRENT_DATE - INTERVAL '9 day', 27, 13, 0.0, 58, 11, 16),

  -- -34.9, -58.0
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '0 day', 29, 15, 3.0, 69, 12, 19),
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '1 day', 28, 14, 2.0, 64, 10, 18),
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '2 day', 27, 13, 0.0, 55, 8,  15),
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '3 day', 30, 16, 1.0, 63, 14, 21),
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '4 day', 26, 12, 5.5, 77, 16, 17),
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '5 day', 25, 11, 7.5, 81, 9,  14),
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '6 day', 31, 17, 2.0, 67, 13, 22),
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '7 day', 29, 15, 1.5, 62, 15, 20),
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '8 day', 28, 14, 0.0, 59, 11, 17),
  (-34.9, -58.0, CURRENT_DATE - INTERVAL '9 day', 27, 13, 0.5, 60, 10, 16);
