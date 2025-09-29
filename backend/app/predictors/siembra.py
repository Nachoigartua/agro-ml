import joblib, pathlib
from datetime import date, timedelta

class SiembraPredictor:
    MODEL_VERSION = '0.3.0'
    def __init__(self):
        self._model = None
    def _load(self):
        if self._model is None:
            path = pathlib.Path(__file__).resolve().parents[2] / 'machine-learning' / 'siembra' / 'models' / 'siembra_rf.joblib'
            if not path.exists():
                raise RuntimeError('Modelo de siembra no entrenado aún. Entrená /ml/train/siembra')
            self._model = joblib.load(path)['model']
    def predict(self, payload: dict):
        self._load()
        coords = payload.get('coords', {}) or {}
        zona = 2
        lat = float(coords.get('latitud', -34.6))
        lon = float(coords.get('longitud', -58.4))
        temp = 18.0
        lluvia = 80.0
        hum_suelo = 25.0
        mo = 2.0
        ciclo = 120
        X = [[zona, lat, lon, temp, lluvia, hum_suelo, mo, ciclo]]
        day = int(round(float(self._model.predict(X)[0])))
        base = date.fromisocalendar(date.today().year, 1, 1)
        fecha = base + timedelta(days=max(0, day-1))
        return {
            'recomendacion_principal': {
                'fecha_optima': fecha.isoformat(),
                'justificacion': ['ventana agroclimática simulada'],
                'confianza': 0.75
            },
            'alternativas': []
        }
