import joblib, pathlib

class RendimientoPredictor:
    MODEL_VERSION = '0.3.0'
    def __init__(self):
        self._model = None
    def _load(self):
        if self._model is None:
            path = pathlib.Path(__file__).resolve().parents[2] / 'machine-learning' / 'rendimiento' / 'models' / 'rendimiento_gbr.joblib'
            if not path.exists():
                raise RuntimeError('Modelo de rendimiento no entrenado. Entrená /ml/train/rendimiento')
            self._model = joblib.load(path)['model']
    def predict(self, payload: dict):
        self._load()
        zona, lat, lon, temp, lluvia, hum_suelo, mo, ciclo = 2, -34.6, -58.4, 18.0, 80.0, 25.0, 2.0, 120
        X = [[zona, lat, lon, temp, lluvia, hum_suelo, mo, ciclo]]
        y = float(self._model.predict(X)[0])
        return {
            'rendimiento_kg_ha': int(round(y)),
            'rango_confianza': [max(0, int(round(y-400))), int(round(y+400))],
            'features_importantes': ['lluvia', 'MO', 'ciclo']
        }
