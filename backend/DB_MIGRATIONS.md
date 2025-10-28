## Migraciones con Alembic

El esquema compartido por la API y el pipeline de ML se versiona con Alembic. Cada cambio estructural debe registrarse como una migración en `backend/alembic/versions/`.

### ¿Cuándo crear una migración?
- **Sí** cuando agregás, eliminás o modificás tablas, columnas, tipos, constraints, índices o relaciones en `backend/api/app/db/models`.
- **No** cuando sólo cambiás lógica Python (servicios, DTOs, tests) sin alterar el esquema de la base.

### Generar una migración nueva
1. Actualizá los modelos SQLAlchemy dentro de `backend/api/app/db/models`.
2. Generá el borrador usando el contenedor del backend:
   ```bash
   docker compose run --rm backend alembic -c /workspace/backend/alembic.ini revision --autogenerate -m "breve descripcion"
   ```
   Se creará un archivo en `backend/alembic/versions/`.
3. Revisá el script y ajustalo si es necesario.
4. Aplicá la migración localmente:
   ```bash
   docker compose run --rm backend alembic -c /workspace/backend/alembic.ini upgrade head
   ```
5. Committeá el archivo generado dentro de `backend/alembic/versions/`.

> El contenedor del backend ejecuta `alembic -c /workspace/backend/alembic.ini upgrade head` al arrancar, así que al hacer `docker compose up backend` la base queda sincronizada automáticamente con la última migración.
