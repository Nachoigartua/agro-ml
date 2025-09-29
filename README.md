# ML Agro - Demo Integrada (Angular + FastAPI + Redis + Postgres)

**Estado**: datos simulados (Finnegans no expone endpoints). Entrenamiento local de modelos con `scikit-learn` y persistencia en disco (`joblib`).

## Puesta en marcha

```bash
docker compose build
docker compose up -d
```

Abrir http://localhost:8080

## Entrenar modelos (vía UI o cURL)

```bash
curl -X POST http://localhost:8080/api/ml/train/siembra -H 'x-api-key: dev-local-key' -H 'Content-Type: application/json' -d '{"modelo":"siembra"}'
```

Modelos se guardan en:
- `backend/machine-learning/siembra/models/siembra_rf.joblib`
- `backend/machine-learning/rendimiento/models/rendimiento_gbr.joblib`
- `backend/machine-learning/variedades/models/variedad_rf.joblib`

## Predicción

Las rutas `/api/ml/predict/...` están rate-limited (60 req/min/ip) y cacheadas en Redis por tipo.

## Esquema DB

Ver `infra/db/init.sql`. Tabla `predicciones` persiste resultados.

## Seguridad

- `x-api-key` obligatoria (configurable por env).
- Nginx añade la cabecera hacia backend por defecto en local.
