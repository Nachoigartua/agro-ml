import joblib, pathlib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
from ..common.simulate import simulate_weather, label_variedad
import pandas as pd

def _prep(df: pd.DataFrame):
    df = df.copy()
    df['cultivo'] = df['cultivo'].map({'maiz':0,'soja':1,'trigo':2})
    df['manejo'] = df['manejo'].map({'bajo':0,'medio':1,'alto':2})
    return df

def train(seed=42, n_samples=2000):
    df = simulate_weather(n_samples, seed=seed)
    y = label_variedad(df)
    df = _prep(df)
    X = df[['zona','lat','lon','temp','lluvia','hum_suelo','mo','ciclo','cultivo','manejo']].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)
    model = RandomForestClassifier(n_estimators=300, random_state=seed)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    f1 = f1_score(y_test, pred, average='macro')
    out_dir = pathlib.Path(__file__).resolve().parents[1] / 'models'
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / 'variedad_rf.joblib'
    joblib.dump({'model': model, 'f1_macro': float(f1)}, model_path)
    return {'path': str(model_path), 'f1_macro': float(f1), 'n': int(n_samples)}

if __name__ == '__main__':
    print(train())
