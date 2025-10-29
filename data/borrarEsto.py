import pandas as pd

# Ruta al archivo original
input_csv = "dataset_completo_argentina.csv"

# Ruta al nuevo archivo convertido
output_csv = "dataset_convertido.csv"

# Leer el CSV
df = pd.read_csv(input_csv)

# Convertir la columna 'dia_del_ano' a datetime y luego al número de día del año
df["dia_del_ano"] = pd.to_datetime(df["dia_del_ano"], errors="coerce").dt.dayofyear

# Guardar el nuevo archivo CSV
df.to_csv(output_csv, index=False)

print("✅ Conversión completa. Archivo guardado en:", output_csv)
print(df[["dia_del_ano"]].head())  # Muestra las primeras filas para verificar
