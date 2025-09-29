import joblib, pathlib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from ..common.simulate import simulate_weather, target_rendimiento
import numpy as np

def train(seed=42, n_samples=2000):
    df = simulate_weather(n_samples, seed=seed)
    y = target_rendimiento(df, seed=seed)
    X = df[['zona','lat','lon','temp','lluvia','hum_suelo','mo','ciclo']].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)
    model = GradientBoostingRegressor(random_state=seed)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    r2 = float(r2_score(y_test, pred))
    out_dir = pathlib.Path(__file__).resolve().parents[1] / 'models'
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / 'rendimiento_gbr.joblib'
    joblib.dump({'model': model, 'rmse': rmse, 'r2': r2}, model_path)
    return {'path': str(model_path), 'rmse': rmse, 'r2': r2, 'n': int(n_samples)}

if __name__ == '__main__':
    print(train())
