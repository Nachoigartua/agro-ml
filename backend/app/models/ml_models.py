from datetime import date
from typing import Dict, Any

class SiembraPredictor:
    """Placeholder de modelo (regla determinística estable) para simular ML con tiempos <30s."""
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        cultivo = features["cultivo"]
        # Simulación determinística por cultivo → DOY base
        doy_base = {"trigo": 250, "soja": 335, "maiz": 300, "cebada": 230}[cultivo]
        # Ajuste leve por latitud si llega
        lat = float(features.get("latitud", -34.6))
        adj = int((abs(lat) - 30) * 0.8)
        doy = max(1, min(365, doy_base - adj))
        fecha = date.fromordinal(date.today().toordinal() - date.today().timetuple().tm_yday + doy)
        return {
            "fecha_optima": fecha,
            "ventana_inicio": fecha,
            "ventana_fin": fecha,
            "confianza": 0.78,
            "riesgos": "Evento de heladas tempranas: bajo; déficit hídrico: medio",
            "alternativas": ["Ajustar fecha ±7 días", "Variedad de ciclo intermedio"],
        }
