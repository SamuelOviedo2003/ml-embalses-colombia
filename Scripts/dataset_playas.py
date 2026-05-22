import pandas as pd

# Ruta del archivo dataset
dataset_path = "../Datasets/dataset_final.csv"

# Leer el dataset
df = pd.read_csv(dataset_path)

# Filtrar solo las playas
df_playas = df[df['CodigoEmbalse'] == 'PLAYAS'].copy()

# Guardar el dataset filtrado
output_path = "../Datasets/dataset_playas.csv"
df_playas.to_csv(output_path, index=False)

print(f"Dataset de playas creado exitosamente: {output_path}")
print(f"Total de registros: {len(df_playas)}")
print(f"\nCódigos de embalse únicos: {df_playas['CodigoEmbalse'].nunique()}")
print(df_playas.head())
