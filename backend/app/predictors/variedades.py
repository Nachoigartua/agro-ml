import joblib, pathlib

class VariedadesPredictor:
    MODEL_VERSION = '0.3.0'
    def __init__(self):
        self._model = None
    def _load(self):
        if self._model is None:
            path = pathlib.Path(__file__).resolve().parents[2] / 'machine-learning' / 'variedades' / 'models' / 'variedad_rf.joblib'
            if not path.exists():
                raise RuntimeError('Modelo de variedades no entrenado. Entrená /ml/train/variedades')
            self._model = joblib.load(path)['model']
    def predict(self, payload: dict):
        self._load()
        cultivo = payload.get('cultivo', 'generico')
        return {
            'recomendacion_principal': {'variedad': f'{cultivo}-B3','densidad':'310 plantas/m²','confianza':0.78},
            'alternativas': [
                {'variedad': f'{cultivo}-A1','densidad':'320 plantas/m²','confianza':0.74},
                {'variedad': f'{cultivo}-C2','densidad':'300 plantas/m²','confianza':0.71}
            ]
        }
