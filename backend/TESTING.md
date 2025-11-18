# Cómo correr los tests

Desde el contenedor backend:

```bash
docker compose build backend        # solo si cambiaste dependencias
docker compose run --rm backend pytest
```

Esto ejecuta la suite completa usando la misma imagen que se despliega. Si ya tenés las dependencias instaladas en tu máquina y preferís correrlo localmente, podés usar `pytest` desde la raíz del proyecto.
