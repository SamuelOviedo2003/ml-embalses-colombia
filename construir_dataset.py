"""
Construcción del dataset final del proyecto.

Pregunta de investigación:
    Dado el Fenómeno del Niño 2026, ¿en qué momentos los embalses colombianos
    alcanzarán niveles críticos con riesgo de déficit energético?

Dataset resultante — una fila por (Fecha, CodigoEmbalse):
    TARGET   : reserva_pct          — % volumen útil diario del embalse (0-100)
    FEATURES : aportes_masa         — caudal total diario en la región (m³)
               media_historica_masa — media histórica del mismo período (m³)
               aportes_vs_media_pct — aportes actuales / media histórica × 100
               oni                  — índice ONI mensual (señal El Niño)
               mei_v2               — índice MEI v2 mensual (señal ENSO multivariada)

Fuentes:
    SIMEM via pydatasimem : reservas, aportes
    Kaggle CSV local      : ENSO.csv (ONI + MEI.v2, 1950-2024) → expandido a diario

ADVERTENCIA: la descarga tarda ~15-20 minutos para el rango completo.
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'API_XM'))
from pydataxm.pydatasimem import VariableSIMEM

# ── Parámetros ────────────────────────────────────────────────────────────────
START_DATE = "2013-01-01"
END_DATE   = "2026-03-31"

BASE_DIR   = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "Datasets")
ENSO_PATH  = os.path.join(OUTPUT_DIR, "ENSO.csv")


# ── Helpers ───────────────────────────────────────────────────────────────────
def paso(n, total, nombre):
    print(f"\n[{n}/{total}] {nombre}...")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. RESERVAS — TARGET
# ═══════════════════════════════════════════════════════════════════════════════
paso(1, 3, "Descargando reservas hidráulicas (VolumenUtilPorcentaje)")

df_res = VariableSIMEM("VolumenUtilPorcentaje", START_DATE, END_DATE).get_data()
df_res = df_res.reset_index()

# Convertir escala 0-1 → 0-100
df_res["reserva_pct"] = df_res["VolumenUtilPorcentaje"] * 100

# Solo columnas necesarias
df_res = df_res[["Fecha", "CodigoEmbalse", "RegionHidrologica", "reserva_pct"]]
df_res["Fecha"] = pd.to_datetime(df_res["Fecha"])

print(f"  Forma: {df_res.shape}")
print(f"  Embalses únicos: {df_res['CodigoEmbalse'].nunique()}")
print(f"  Rango fechas: {df_res['Fecha'].min().date()} → {df_res['Fecha'].max().date()}")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. APORTES — FEATURE
# ═══════════════════════════════════════════════════════════════════════════════
paso(2, 3, "Descargando aportes hídricos (AportesHidricosMasa)")

df_ap = VariableSIMEM("AportesHidricosMasa", START_DATE, END_DATE).get_data()
df_ap = df_ap.reset_index()
df_ap["Fecha"] = pd.to_datetime(df_ap["Fecha"])

# Agregar por (Fecha, RegionHidrologica) — suma de todas las series de la región
# Así podemos hacer join con reservas que también tiene RegionHidrologica
df_ap_region = (
    df_ap
    .groupby(["Fecha", "RegionHidrologica"])
    .agg(
        aportes_masa=("AportesHidricosMasa", "sum"),
        media_historica_masa=("MediaHistoricaMasa", "sum")
    )
    .reset_index()
)

# % aportes vs media histórica — qué tan seco está el período respecto a lo normal
# Si < 100 → por debajo de lo normal (señal de sequía)
# Si > 100 → por encima de lo normal (año húmedo)
df_ap_region["aportes_vs_media_pct"] = (
    df_ap_region["aportes_masa"]
    / df_ap_region["media_historica_masa"].replace(0, pd.NA)
    * 100
)

print(f"  Forma: {df_ap_region.shape}")
print(f"  Regiones únicas: {df_ap_region['RegionHidrologica'].nunique()}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ONI — FEATURE (CSV local, mensual → diario)
# ═══════════════════════════════════════════════════════════════════════════════
paso(3, 3, "Procesando índice ENSO (ONI + MEI.v2)")

df_enso = pd.read_csv(ENSO_PATH, parse_dates=["Date"])
df_enso = (
    df_enso[["Date", "ONI", "MEI.v2"]]
    .rename(columns={"Date": "Fecha", "ONI": "oni", "MEI.v2": "mei_v2"})
)

# Expandir de mensual a diario: repetir el valor del mes para cada día
df_oni = (
    df_enso
    .set_index("Fecha")
    .resample("D")        # crear una fila por día
    .ffill()              # propagar el valor mensual hacia adelante
    .reset_index()
)

# Recortar al rango del proyecto
df_oni = df_oni[
    (df_oni["Fecha"] >= START_DATE) &
    (df_oni["Fecha"] <= END_DATE)
]

print(f"  Forma: {df_oni.shape}")
print(f"  Rango fechas: {df_oni['Fecha'].min().date()} → {df_oni['Fecha'].max().date()}")
print(f"  ONI   min: {df_oni['oni'].min():.2f} | max: {df_oni['oni'].max():.2f}")
print(f"  MEI.v2 nulos: {df_oni['mei_v2'].isnull().sum()}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MERGE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[Merge] Uniendo datasets...")

# Base: reservas — una fila por (Fecha, CodigoEmbalse)
df = df_res.copy()

# Aportes: join por (Fecha, RegionHidrologica)
# Cada embalse recibe los aportes agregados de su región
df = df.merge(df_ap_region, on=["Fecha", "RegionHidrologica"], how="left")

# ONI: join por Fecha — broadcast a todos los embalses del mismo día
df = df.merge(df_oni, on="Fecha", how="left")

# Orden de columnas
df = df[[
    "Fecha",
    "CodigoEmbalse",
    "RegionHidrologica",
    "reserva_pct",           # TARGET
    "aportes_masa",          # features
    "media_historica_masa",
    "aportes_vs_media_pct",
    "oni",
    "mei_v2",
]]

df = df.sort_values(["Fecha", "CodigoEmbalse"]).reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. GUARDAR
# ═══════════════════════════════════════════════════════════════════════════════
output_path = os.path.join(OUTPUT_DIR, "dataset_final.csv")
df.to_csv(output_path, index=False)

print(f"\n{'='*60}")
print(f"  Dataset final guardado en: {output_path}")
print(f"{'='*60}")
print(f"  Filas      : {len(df):,}")
print(f"  Columnas   : {list(df.columns)}")
print(f"  Embalses   : {df['CodigoEmbalse'].nunique()}")
print(f"  Regiones   : {df['RegionHidrologica'].nunique()}")
print(f"  Rango      : {df['Fecha'].min().date()} → {df['Fecha'].max().date()}")
print(f"\n--- Primeras filas ---")
print(df.head(10).to_string())
print(f"\n--- Valores nulos por columna ---")
print(df.isnull().sum())
