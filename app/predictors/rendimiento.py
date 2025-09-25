import random
class RendimientoPredictor:
  MODEL_VERSION='0.2.0'
  def predict(self,p, suelo_mo: float = 2.0, temp_media: float = 18.0, pp_mm: float = 80.0):
    base = 4200
    base += int((suelo_mo - 2.0) * 150)
    base += int((temp_media - 18.0) * 20)
    base += int((pp_mm - 70.0) * 5)
    ruido = random.randint(-200,200)
    pred = max(0, base + ruido)
    return {'rendimiento_kg_ha': pred,'rango_confianza': [max(0, pred-250), pred+250],'factores_clave': ['lluvia estacional','materia orgánica','temperatura media']}
