from datetime import date,timedelta
class SiembraPredictor:
  MODEL_VERSION='0.2.0'
  def predict(self,p):
    base=date.fromisoformat(p.get('fecha_referencia',f"{date.today().year}-10-01"))
    lat=p['coords']['latitud']; off=int(abs(lat)%10)
    f=base+timedelta(days=off)
    return {'recomendacion_principal':{'fecha_optima':f.isoformat(),'ventana':[(f-timedelta(days=5)).isoformat(),(f+timedelta(days=5)).isoformat()],'confianza':0.85},'alternativas':[{'fecha':(f+timedelta(days=10)).isoformat(),'pros':['Mayor humedad esperada'],'contras':['Riesgo de heladas tardías'],'confianza':0.72}]}
