class Metrics:
    def __init__(self):
        self.prediction_times = {}
        self.calls = {}
    def track(self, model, elapsed):
        self.prediction_times.setdefault(model, []).append(elapsed)
        self.calls[model] = self.calls.get(model, 0) + 1
    def snapshot(self):
        return {'calls': self.calls,'avg_prediction_ms': {k:(sum(v)/len(v))*1000 for k,v in self.prediction_times.items() if v}}
metrics = Metrics()
