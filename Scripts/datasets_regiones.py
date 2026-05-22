import pandas as pd
from pathlib import Path

# Ruta al archivo original
base_path = Path(__file__).resolve().parent
csv_path = base_path.parent / "Datasets" / "dataset_final.csv"

# Leer el dataset
try:
    df = pd.read_csv(csv_path)
except FileNotFoundError:
    raise FileNotFoundError(f"No se encontró el archivo: {csv_path}")

# Verificar que exista la columna RegionHidrologica
region_columns = [c for c in df.columns if c == "RegionHidrologica"]
if not region_columns:
    raise ValueError("No se encontró una columna de región en el dataset.")
region_col = region_columns[0]

# Guardar un csv por cada región en la misma carpeta del dataset original
output_dir = csv_path.parent
for region, group in df.groupby(region_col):
    if pd.isna(region):
        filename = "dataset_region_desconocida.csv"
    else:
        safe_region = str(region).strip().replace("/", "_").replace("\\", "_").replace(" ", "_")
        filename = f"dataset_region_{safe_region}.csv"
    output_path = output_dir / filename
    group.to_csv(output_path, index=False)

print(f"Se crearon {len(df[region_col].dropna().unique())} archivos CSV en: {output_dir}")
