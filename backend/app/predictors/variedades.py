class VariedadesPredictor:
    MODEL_VERSION = '0.2.0'
    def predict(self, payload):
        cultivo = payload.get('cultivo', 'generico')
        objetivos = (payload.get('objetivos') or [])
        if any('alto' in o for o in objetivos):
            principal = {"variedad": f"{cultivo}-A1", "densidad":"320 plantas/m²", "justificacion":["alto potencial","buena sanidad"], "confianza":0.84}
            alts = [{"variedad": f"{cultivo}-B3","densidad":"300 plantas/m²", "justificacion":["estabilidad"], "confianza":0.78}]
        elif any('bajo_riesgo' in o for o in objetivos):
            principal = {"variedad": f"{cultivo}-C2","densidad":"300 plantas/m²", "justificacion":["tolerancia a estrés","ciclo intermedio"], "confianza":0.80}
            alts = [{"variedad": f"{cultivo}-B3","densidad":"290 plantas/m²", "justificacion":["estabilidad"], "confianza":0.76}]
        else:
            principal = {"variedad": f"{cultivo}-B3","densidad":"310 plantas/m²", "justificacion":["estabilidad","sanidad"], "confianza":0.82}
            alts = [{"variedad": f"{cultivo}-A1","densidad":"320 plantas/m²", "justificacion":["alto potencial"], "confianza":0.77}]
        return {"recomendacion_principal": principal, "alternativas": alts}
