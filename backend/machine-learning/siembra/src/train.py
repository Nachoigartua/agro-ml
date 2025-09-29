import joblib, pathlib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from ..common.simulate import simulate_weather, fecha_siembra

def train(seed=42, n_samples=2000):
    df = simulate_weather(n_samples, seed=seed)
    y = fecha_siembra(df, seed=seed)
    X = df[['zona','lat','lon','temp','lluvia','hum_suelo','mo','ciclo']].values
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)
    model = RandomForestRegressor(n_estimators=200, random_state=seed)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    out_dir = pathlib.Path(__file__).resolve().parents[1] / 'models'
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / 'siembra_rf.joblib'
    joblib.dump({'model': model, 'mae': float(mae)}, model_path)
    return {'path': str(model_path), 'mae': float(mae), 'n': int(n_samples)}

if __name__ == '__main__':
    print(train())
