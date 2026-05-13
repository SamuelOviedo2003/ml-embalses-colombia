import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================================================
# CONFIGURACIÓN
# =========================================================

FILE_PATH = "./Datasets/dataset_final.csv"

# Llave lógica esperada del dataset
KEY_COLUMNS = ["Fecha", "CodigoEmbalse"]

# =========================================================
# CARGA DEL DATASET
# =========================================================

print("=" * 60)
print("CARGANDO DATASET")
print("=" * 60)

df = pd.read_csv(FILE_PATH)

# Filtrado de datos
df = df[~df["CodigoEmbalse"].isin(["AGREGADO_SIN", "ITUANGO", "SOGAMOSO", "ELQUIMBO"])]

df["Fecha"] = pd.to_datetime(df["Fecha"])


print(f"\nCantidad total de registros: {len(df):,}")
print(f"Cantidad total de columnas: {len(df.columns)}")

# =========================================================
# CONVERSIÓN DE FECHA
# =========================================================

print("\n" + "=" * 60)
print("CONVERSIÓN DE FECHAS")
print("=" * 60)

df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

print("\nTipo de dato Fecha:")
print(df["Fecha"].dtype)

print("\nRango temporal:")
print("Min:", df["Fecha"].min())
print("Max:", df["Fecha"].max())

# =========================================================
# INFORMACIÓN GENERAL
# =========================================================

print("\n" + "=" * 60)
print("INFO GENERAL")
print("=" * 60)

print("\nTipos de datos:")
print(df.dtypes)

print("\nValores nulos:")
print(df.isnull().sum())

# =========================================================
# DUPLICADOS EXACTOS
# =========================================================

print("\n" + "=" * 60)
print("DUPLICADOS EXACTOS")
print("=" * 60)

exact_duplicates = df.duplicated().sum()

print(f"\nDuplicados exactos: {exact_duplicates:,}")

# =========================================================
# DUPLICADOS POR LLAVE LÓGICA
# =========================================================

print("\n" + "=" * 60)
print("DUPLICADOS POR LLAVE LÓGICA")
print("=" * 60)

logical_duplicates = df.duplicated(subset=KEY_COLUMNS, keep=False)

dup_df = df[logical_duplicates].sort_values(KEY_COLUMNS)

print(f"\nRegistros duplicados por llave lógica: {len(dup_df):,}")

if len(dup_df) > 0:
    print("\nPrimeros duplicados encontrados:")
    print(dup_df.head(20))

# =========================================================
# CONTEO POR GRUPO
# =========================================================

print("\n" + "=" * 60)
print("CONTEO POR GRUPO")
print("=" * 60)

group_counts = df.groupby(KEY_COLUMNS).size().reset_index(name="count")

problematic_groups = group_counts[group_counts["count"] > 1]

print(f"\nCantidad de grupos problemáticos: {len(problematic_groups):,}")

if len(problematic_groups) > 0:
    print("\nPrimeros grupos problemáticos:")
    print(problematic_groups.head(20))

# =========================================================
# VERIFICACIÓN DE EMBALSES
# =========================================================

print("\n" + "=" * 60)
print("EMBALSES")
print("=" * 60)

unique_embalses = df["CodigoEmbalse"].nunique()

print(f"\nCantidad de df únicos: {unique_embalses}")

print("\nEmbalses con más registros:")

embalse_counts = df["CodigoEmbalse"].value_counts()

print(embalse_counts.head(20))

# =========================================================
# VERIFICACIÓN TEMPORAL
# =========================================================

print("\n" + "=" * 60)
print("VERIFICACIÓN TEMPORAL")
print("=" * 60)

date_counts = df.groupby("Fecha").size().reset_index(name="count")

print("\nFechas con más registros:")
print(date_counts.sort_values("count", ascending=False).head(20))

# =========================================================
# ESPERADO VS REAL
# =========================================================

print("\n" + "=" * 60)
print("ESPERADO VS REAL")
print("=" * 60)

num_days = df["Fecha"].nunique()
num_embalses = df["CodigoEmbalse"].nunique()

expected_records = num_days * num_embalses
real_records = len(df)

print(f"\nDías únicos: {num_days:,}")
print(f"Embalses únicos: {num_embalses:,}")

print(f"\nRegistros esperados: {expected_records:,}")
print(f"Registros reales: {real_records:,}")

difference = real_records - expected_records

print(f"\nDiferencia: {difference:,}")

# =========================================================
# REVISIÓN DE COLUMNAS CONSTANTES
# =========================================================

print("\n" + "=" * 60)
print("COLUMNAS CONSTANTES")
print("=" * 60)

constant_columns = []

for col in df.columns:
    unique_vals = df[col].nunique(dropna=False)

    if unique_vals <= 1:
        constant_columns.append(col)

if constant_columns:
    print("\nColumnas constantes:")
    print(constant_columns)
else:
    print("\nNo se encontraron columnas constantes")

# =========================================================
# OUTLIERS BÁSICOS
# =========================================================

print("\n" + "=" * 60)
print("OUTLIERS BÁSICOS")
print("=" * 60)

numeric_cols = df.select_dtypes(include=np.number).columns

for col in numeric_cols:

    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)

    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outliers = ((df[col] < lower) | (df[col] > upper)).sum()

    print(f"{col}: {outliers:,} outliers")

# =========================================================
# VERIFICACIÓN DE NULOS POR FILA
# =========================================================

print("\n" + "=" * 60)
print("FILAS CON MUCHOS NULOS")
print("=" * 60)

df["null_count"] = df.isnull().sum(axis=1)

print("\nDistribución de nulos por fila:")
print(df["null_count"].value_counts().sort_index())

# =========================================================
# CREACIÓN DE HASH / KEY
# =========================================================

print("\n" + "=" * 60)
print("HASH DE LLAVE")
print("=" * 60)

df["unique_key"] = df["Fecha"].astype(str) + "_" + df["CodigoEmbalse"].astype(str)

duplicate_keys = df["unique_key"].duplicated().sum()

print(f"\nLlaves duplicadas: {duplicate_keys:,}")

# =========================================================
# ESTADÍSTICAS GENERALES
# =========================================================

print("\n" + "=" * 60)
print("ESTADÍSTICAS GENERALES")
print("=" * 60)

print(df.describe())

# =========================================================
# EXPORTAR DUPLICADOS
# =========================================================

if len(dup_df) > 0:

    dup_df.to_csv("duplicados_detectados.csv", index=False)

    print("\nArchivo generado:")
    print("duplicados_detectados.csv")

# =========================================================
# GRÁFICO DE REGISTROS POR FECHA
# =========================================================

print("\n" + "=" * 60)
print("GENERANDO GRÁFICO")
print("=" * 60)

plt.figure(figsize=(15, 5))

plt.plot(date_counts["Fecha"], date_counts["count"])

plt.title("Cantidad de registros por fecha")
plt.xlabel("Fecha")
plt.ylabel("Cantidad de registros")

plt.tight_layout()

plt.savefig("registros_por_fecha.png")

print("\nGráfico guardado:")
print("registros_por_fecha.png")

# =========================================================
# FINAL
# =========================================================

print("\n" + "=" * 60)
print("AUDITORÍA FINALIZADA")
print("=" * 60)
