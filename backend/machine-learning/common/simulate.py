import numpy as np
import pandas as pd

def simulate_weather(n, seed=42):
    rng = np.random.default_rng(seed)
    zona = rng.integers(0, 5, size=n)
    lat = rng.uniform(-45, -20, size=n)
    lon = rng.uniform(-70, -55, size=n)
    temp = rng.normal(18, 4, size=n) + (lat + 45) * 0.05
    lluvia = np.clip(rng.normal(80, 30, size=n), 0, None)
    hum_suelo = np.clip(rng.normal(25, 8, size=n), 5, 60)
    mo = np.clip(rng.normal(2.2, 0.6, size=n), 0.5, 6)
    ciclo = rng.integers(90, 140, size=n)
    cultivo = rng.choice(['maiz','soja','trigo'], size=n, p=[0.4,0.4,0.2])
    manejo = rng.choice(['bajo','medio','alto'], size=n, p=[0.3,0.5,0.2])

    df = pd.DataFrame({
        'zona': zona, 'lat': lat, 'lon': lon, 'temp': temp, 'lluvia': lluvia,
        'hum_suelo': hum_suelo, 'mo': mo, 'ciclo': ciclo,
        'cultivo': cultivo, 'manejo': manejo
    })
    return df

def target_rendimiento(df: pd.DataFrame, seed=42):
    rng = np.random.default_rng(seed)
    base = 3000 + 20*df['lluvia'] + 50*df['mo'] + 10*df['temp'] + 5*df['ciclo']
    manejo_bonus = df['manejo'].map({'bajo':-200,'medio':0,'alto':300}).fillna(0)
    cultivo_adj = df['cultivo'].map({'maiz':400,'soja':0,'trigo':200}).fillna(0)
    ruido = rng.normal(0, 300, size=len(df))
    y = np.clip(base + manejo_bonus + cultivo_adj + ruido, 0, None)
    return y

def label_variedad(df: pd.DataFrame):
    code = (df['zona'] % 3).map({0:'A',1:'B',2:'C'})
    return (df['cultivo'].str[:1].str.upper() + code)

def fecha_siembra(df: pd.DataFrame, seed=42):
    rng = np.random.default_rng(seed)
    base = 250 - (df['temp'] - 18) * 4 + (df['zona'] * 2)
    base += np.where(df['lluvia']>100, -10, 5)
    ruido = rng.normal(0, 7, size=len(df))
    day = np.clip(np.round(base + ruido), 200, 330).astype(int)
    return day
