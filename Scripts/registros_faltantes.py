import pandas as pd

# ======================================================
# CARGAR
# ======================================================

df = pd.read_csv("./Datasets/dataset_final.csv")

# Filtrado de datos
df = df[~df["CodigoEmbalse"].isin(["AGREGADO_SIN", "ITUANGO", "SOGAMOSO"])]

df["Fecha"] = pd.to_datetime(df["Fecha"])


df["Fecha"] = pd.to_datetime(df["Fecha"])

# ======================================================
# RANGO COMPLETO DE FECHAS
# ======================================================

all_dates = pd.date_range(start=df["Fecha"].min(), end=df["Fecha"].max(), freq="D")

all_embalses = df["CodigoEmbalse"].unique()

# ======================================================
# CREAR TODAS LAS COMBINACIONES ESPERADAS
# ======================================================

expected = pd.MultiIndex.from_product(
    [all_dates, all_embalses], names=["Fecha", "CodigoEmbalse"]
).to_frame(index=False)

# ======================================================
# HACER MERGE
# ======================================================

merged = expected.merge(
    df[["Fecha", "CodigoEmbalse"]],
    on=["Fecha", "CodigoEmbalse"],
    how="left",
    indicator=True,
)

# ======================================================
# FILAS FALTANTES
# ======================================================

missing = merged[merged["_merge"] == "left_only"]

print("=" * 60)
print("REGISTROS FALTANTES")
print("=" * 60)

print(f"\nCantidad faltante: {len(missing):,}")

print("\nPrimeros faltantes:")
print(missing.head(20))

# ======================================================
# FALTANTES POR EMBALSE
# ======================================================

print("\n" + "=" * 60)
print("FALTANTES POR EMBALSE")
print("=" * 60)

missing_by_embalse = (
    missing.groupby("CodigoEmbalse").size().sort_values(ascending=False)
)

print(missing_by_embalse)

# ======================================================
# FALTANTES POR FECHA
# ======================================================

print("\n" + "=" * 60)
print("FALTANTES POR FECHA")
print("=" * 60)

missing_by_date = missing.groupby("Fecha").size().sort_values(ascending=False)

print(missing_by_date.head(20))


availability = df.groupby("CodigoEmbalse").agg(
    fecha_inicio=("Fecha", "min"),
    fecha_fin=("Fecha", "max"),
    registros=("Fecha", "count"),
)

print("################################")
print(availability)
