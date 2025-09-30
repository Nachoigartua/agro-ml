# Sistema de Machine Learning para Optimización Agrícola

Sistema de ML integrado que genera recomendaciones inteligentes para optimizar decisiones agrícolas basadas en datos históricos, condiciones climáticas y características del suelo.

## 🌾 Características Principales

- **Recomendaciones de Siembra**: Fechas óptimas basadas en clima y suelo
- **Selección de Variedades**: Variedades más adecuadas por lote
- **Predicciones Climáticas**: Lluvia y temperatura (mensual/estacional)
- **Optimización de Fertilización**: Planes de fertilización por lote
- **Predicción de Rendimientos**: Estimación de rendimientos esperados
- **Optimización de Cosecha**: Momentos óptimos de cosecha

## 🏗️ Arquitectura
┌─────────────┐
│   Nginx     │ :8080
└──────┬──────┘
│
┌───┴────────────┐
│                │
┌──▼───────┐  ┌────▼────┐
│ Frontend │  │ Backend │
│ Angular  │  │ FastAPI │
└──────────┘  └────┬────┘
│
┌─────────┴─────────┐
│                   │
┌────▼─────┐      ┌─────▼────┐
│PostgreSQL│      │  Redis   │
│ + PostGIS│      │  Cache   │
└──────────┘      └──────────┘

## 🚀 Inicio Rápido

### Prerequisitos

- Docker y Docker Compose
- Git

### Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/Nachoigartua/agro-ml.git
cd agro-ml
git checkout demo-v2

Configurar variables de entorno

bashcp .env.example .env
# Editar .env según necesidades

Construir y levantar servicios

bashdocker compose build
docker compose up -d

Verificar que todo esté corriendo

bashdocker compose ps

Acceder a la aplicación


Frontend: http://localhost:8080
Backend API: http://localhost:8080/api/docs
Swagger UI: http://localhost:8080/api/docs

📊 Entrenamiento de Modelos
Entrenar todos los modelos
bashcurl -X POST http://localhost:8080/api/ml/train/siembra \
  -H 'x-api-key: dev-local-key' \
  -H 'Content-Type: application/json' \
  -d '{"force_retrain": true}'

curl -X POST http://localhost:8080/api/ml/train/variedades \
  -H 'x-api-key: dev-local-key' \
  -H 'Content-Type: application/json' \
  -d '{"force_retrain": true}'

curl -X POST http://localhost:8080/api/ml/train/rendimiento \
  -H 'x-api-key: dev-local-key' \
  -H 'Content-Type: application/json' \
  -d '{"force_retrain": true}'

curl -X POST http://localhost:8080/api/ml/train/fertilizacion \
  -H 'x-api-key: dev-local-key' \
  -H 'Content-Type: application/json' \
  -d '{"force_retrain": true}'

curl -X POST http://localhost:8080/api/ml/train/clima \
  -H 'x-api-key: dev-local-key' \
  -H 'Content-Type: application/json' \
  -d '{"force_retrain": true}'

curl -X POST http://localhost:8080/api/ml/train/cosecha \
  -H 'x-api-key: dev-local-key' \
  -H 'Content-Type: application/json' \
  -d '{"force_retrain": true}'
🔧 Uso del Sistema
Hacer una predicción de siembra
bashcurl -X POST http://localhost:8080/api/ml/predict/siembra \
  -H 'x-api-key: dev-local-key' \
  -H 'Content-Type: application/json' \
  -d '{
    "lote_id": "lote-001",
    "cliente_id": "cliente-001",
    "cultivo": "trigo",
    "campana": "2024/2025"
  }'
Hacer una predicción de rendimiento
bashcurl -X POST http://localhost:8080/api/ml/predict/rendimiento \
  -H 'x-api-key: dev-local-key' \
  -H 'Content-Type: application/json' \
  -d '{
    "lote_id": "lote-001",
    "cliente_id": "cliente-001",
    "cultivo": "soja",
    "fecha_siembra": "2024-10-15",
    "variedad": "DM4670"
  }'
🧪 Testing
bash# Ejecutar tests del backend
docker compose exec backend pytest tests/ -v

# Con cobertura
docker compose exec backend pytest tests/ --cov=. --cov-report=html
📁 Estructura del Proyecto
agro-ml/
├── backend/              # API FastAPI + ML Models
│   ├── api/             # Endpoints y modelos
│   ├── ml/              # Modelos de Machine Learning
│   ├── services/        # Lógica de negocio
│   ├── database/        # Conexión y repositorios
│   └── utils/           # Utilidades
├── frontend/            # Aplicación Angular
│   └── src/
│       └── app/
│           ├── core/    # Servicios core
│           ├── shared/  # Componentes compartidos
│           └── features/# Módulos de funcionalidad
├── infra/               # Infraestructura
│   ├── nginx/          # Configuración Nginx
│   └── db/             # Scripts de base de datos
└── tests/              # Tests automatizados
🔌 Integración con Finnegans
El sistema está preparado para integrarse con la API de Finnegans cuando esté disponible:

Modo Desarrollo (actual): USE_MOCK_DATA=true

Usa datos simulados generados localmente
Permite testing completo sin dependencias externas


Modo Producción (futuro): USE_MOCK_DATA=false

Se conecta a la API real de Finnegans
Configurar FINNEGANS_API_URL y FINNEGANS_API_KEY en .env



Configuración para producción
envUSE_MOCK_DATA=false
FINNEGANS_API_URL=https://api.finnegans.com
FINNEGANS_API_KEY=your-production-api-key
📦 Modelos Almacenados
Los modelos entrenados se guardan en:
ml_models/
├── siembra_rf.joblib
├── variedades_xgb.joblib
├── rendimiento_gbr.joblib
├── fertilizacion_multi.joblib
├── clima_lstm.joblib
└── cosecha_rf.joblib
🔒 Seguridad

API Key: Todas las rutas requieren header x-api-key
Rate Limiting: 60 requests/minuto por IP
CORS: Configurado para orígenes permitidos
Validación: Validación estricta de datos de entrada

📊 Monitoreo
Ver logs
bash# Todos los servicios
docker compose logs -f

# Solo backend
docker compose logs -f backend

# Solo frontend
docker compose logs -f frontend
Estado de modelos
bashcurl http://localhost:8080/api/ml/models/status \
  -H 'x-api-key: dev-local-key'
Health check
bashcurl http://localhost:8080/api/health
🛠️ Troubleshooting
Problema: Los modelos no se entrenan
Solución: Verificar que existan datos mock
bashdocker compose exec backend python -c "from services.data_mock_service import DataMockService; print(DataMockService().get_mock_lotes_data())"
Problema: Frontend no se conecta al backend
Solución: Verificar variables de entorno
bash# Verificar que NGINX esté redirigiendo correctamente
docker compose logs nginx
Problema: Cache no funciona
Solución: Verificar Redis
bashdocker compose exec redis redis-cli ping
# Debe responder: PONG
📝 Criterios de Aceptación
✅ Funcionales

 Sistema genera recomendaciones para todos los módulos
 Integración con mock data funcionando
 API RESTful documentada (Swagger)
 Tiempo de respuesta < 30 segundos

✅ Técnicos

 Dockerizado y orquestado con Docker Compose
 Base de datos PostgreSQL con PostGIS
 Cache con Redis
 Rate limiting implementado
 Logging estructurado
 API key authentication

✅ Calidad

 Modelos entrenados localmente
 Datos mock para testing
 Sistema preparado para API real de Finnegans
 Documentación completa

📄 Licencia
Proyecto privado - Todos los derechos reservados
