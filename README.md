# agro-ml
Un sistema de Machine Learning que se integra como módulo adicional a un sistema agrícola existente de Finnegans, proporcionando recomendaciones inteligentes para optimizar decisiones agrícolas basadas en datos históricos, condiciones climáticas y características del suelo.

## Entrenar el modelo
- Una vez levantados los contenedores, ejecuta `docker compose exec backend python /workspace/backend/machine-learning/train_siembra_model.py` para entrenar el modelo y persistirlo en la base de datos.
