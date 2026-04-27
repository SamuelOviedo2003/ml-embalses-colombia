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
               t2m                  — temperatura a 2m (°C)
               u10                  — viento componente zonal a 10m (m/s)
               v10                  — viento componente meridional a 10m (m/s)
               msl                  — presión al nivel del mar (hPa)
               sst                  — temperatura superficial del mar (°C)
               tp                   — precipitación total (mm)
               ro                   — escorrentía total (mm)
               sro                  — escorrentía superficial (mm)
               swvl1                — humedad volumétrica suelo capa 1 (m³/m³)
               wind_speed           — velocidad del viento (m/s)

Fuentes:
    SIMEM via pydatasimem : reservas, aportes
    ERA5 .grib local      : variables climáticas (0.25° resolución)
"""

import pandas as pd
import numpy as np
import xarray as xr
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "API_XM"))
from pydataxm.pydatasimem import VariableSIMEM

# ── Parámetros ────────────────────────────────────────────────────────────────
START_DATE = "2013-01-01"
END_DATE = "2024-12-31"

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "Datasets")
GRIB_PATH = os.path.join(
    OUTPUT_DIR, "combinado.grib"
)  # ← ajusta si el .grib está en otra ruta

# Coordenadas de cada embalse (punto de grilla ERA5 más cercano)
COORDENADAS_EMBALSES = {
    "ALTOANCH": {"lat": 3.90, "lon": -76.88},
    "BETANIA": {"lat": 2.685, "lon": -75.44},
    "CALIMA1": {"lat": 3.92, "lon": -76.48},
    "CHUZA": {"lat": 4.78, "lon": -73.98},
    "ESMERALD": {"lat": 5.63, "lon": -74.88},
    "GUAVIO": {"lat": 4.72, "lon": -73.49},
    "MIEL1": {"lat": 5.65, "lon": -74.88},
    "MIRAFLOR": {"lat": 6.52, "lon": -75.55},
    "MUNA": {"lat": 4.57, "lon": -74.22},
    "PENOL": {"lat": 6.25, "lon": -75.17},
    "PLAYAS": {"lat": 6.43, "lon": -75.07},
    "PORCE2": {"lat": 6.92, "lon": -75.05},
    "PORCE3": {"lat": 7.13, "lon": -74.98},
    "PRADO": {"lat": 3.75, "lon": -74.92},
    "PUNCHINA": {"lat": 6.00, "lon": -74.65},
    "RIOGRAN2": {"lat": 6.10, "lon": -75.58},
    "SALVAJIN": {"lat": 2.876, "lon": -76.688},
    "SANLOREN": {"lat": 6.38, "lon": -75.37},
    "TRONERAS": {"lat": 6.68, "lon": -75.35},
    "URRA1": {"lat": 7.94, "lon": -76.29},
    "SOGAMOSO": {"lat": 7.101, "lon": -73.407},
    "ELQUIMBO": {"lat": 2.458, "lon": -75.571},
    "ITUANGO": {"lat": 7.132, "lon": -75.664},
    "AGREGADO_BOGOTA": {"lat": 4.493, "lon": -74.260},
}

DROP_COORDS = ["step", "valid_time", "number", "surface", "depthBelowLandLayer"]


# ── Helpers ───────────────────────────────────────────────────────────────────
def paso(n, total, nombre):
    print(f"\n[{n}/{total}] {nombre}...")


def get_nearest_era5(ds_era5, lat, lon):
    """Extrae la serie temporal del punto de grilla ERA5 más cercano a (lat, lon)."""
    lats = ds_era5["latitude"].values
    lons = ds_era5["longitude"].values
    nearest_lat = lats[np.argmin(np.abs(lats - lat))]
    nearest_lon = lons[np.argmin(np.abs(lons - lon))]
    return ds_era5.sel(latitude=nearest_lat, longitude=nearest_lon)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. RESERVAS — TARGET
# ═══════════════════════════════════════════════════════════════════════════════
paso(1, 4, "Descargando reservas hidráulicas (VolumenUtilPorcentaje)")

df_res = VariableSIMEM("VolumenUtilPorcentaje", START_DATE, END_DATE).get_data()
df_res = df_res.reset_index()

df_res["reserva_pct"] = df_res["VolumenUtilPorcentaje"] * 100
df_res = df_res[["Fecha", "CodigoEmbalse", "RegionHidrologica", "reserva_pct"]]
df_res["Fecha"] = pd.to_datetime(df_res["Fecha"])

# Excluir agregado nacional (no tiene embalse físico propio)
df_res = df_res[df_res["CodigoEmbalse"] != "AGREGADO_SIN"]

print(f"  Forma: {df_res.shape}")
print(f"  Embalses únicos: {df_res['CodigoEmbalse'].nunique()}")
print(
    f"  Rango fechas: {df_res['Fecha'].min().date()} → {df_res['Fecha'].max().date()}"
)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. APORTES — FEATURE
# ═══════════════════════════════════════════════════════════════════════════════
paso(2, 3, "Descargando aportes hídricos (AportesHidricosMasa)")

df_ap = VariableSIMEM("AportesHidricosMasa", START_DATE, END_DATE).get_data()
df_ap = df_ap.reset_index()
df_ap["Fecha"] = pd.to_datetime(df_ap["Fecha"])

df_ap["AportesHidricosMasa"] = pd.to_numeric(
    df_ap["AportesHidricosMasa"], errors="coerce"
)
df_ap["MediaHistoricaMasa"] = pd.to_numeric(
    df_ap["MediaHistoricaMasa"], errors="coerce"
)

# Agregar por (Fecha, RegionHidrologica) — suma de todas las series de la región
# Así podemos hacer join con reservas que también tiene RegionHidrologica
df_ap_region = (
    df_ap.groupby(["Fecha", "RegionHidrologica"])
    .agg(
        aportes_masa=("AportesHidricosMasa", "sum"),
        media_historica_masa=("MediaHistoricaMasa", "sum"),
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
# 3. ERA5 — FEATURES CLIMÁTICAS (desde .grib)
# ═══════════════════════════════════════════════════════════════════════════════
paso(3, 4, f"Cargando variables ERA5 desde {GRIB_PATH}")

VARIABLES_GRIB = {
    "t2m": {"shortName": "2t"},
    "u10": {"shortName": "10u"},
    "v10": {"shortName": "10v"},
    "msl": {"shortName": "msl"},
    "tp": {"shortName": "tp"},
    "ro": {"shortName": "ro"},
    "sro": {"shortName": "sro"},
    "swvl1": {"shortName": "swvl1"},
}

datasets_era5 = []
for var_name, keys in VARIABLES_GRIB.items():
    try:
        ds_var = xr.open_dataset(
            GRIB_PATH,
            engine="cfgrib",
            backend_kwargs={"filter_by_keys": keys},
        )
        coords_to_drop = [c for c in DROP_COORDS if c in ds_var.coords]
        ds_var = ds_var.drop_vars(coords_to_drop)
        datasets_era5.append(ds_var)
        print(f"  ✓ {var_name}")
    except Exception as e:
        print(f"  ✗ {var_name} falló: {e}")

ds_era5 = xr.merge(datasets_era5, join="override", compat="override")

# Normalizar tiempo ERA5 a fecha sin hora (para hacer join por día)
ds_era5 = ds_era5.assign_coords(time=ds_era5["time"].dt.floor("D"))

print(f"  Dataset ERA5 cargado: {ds_era5}")

# Extraer punto más cercano para cada embalse y construir DataFrame
print("\n  Extrayendo punto de grilla por embalse...")
dfs_era5 = []

for codigo, coords in COORDENADAS_EMBALSES.items():
    try:
        ds_punto = get_nearest_era5(ds_era5, coords["lat"], coords["lon"])
        df_punto = ds_punto.to_dataframe().reset_index()[
            ["time", "t2m", "u10", "v10", "msl", "tp", "ro", "sro", "swvl1"]
        ]
        df_punto = df_punto.rename(columns={"time": "Fecha"})
        df_punto["CodigoEmbalse"] = codigo

        # Conversiones de unidades
        df_punto["t2m"] = df_punto["t2m"] - 273.15  # K → °C
        df_punto["msl"] = df_punto["msl"] / 100  # Pa → hPa
        df_punto["tp"] = df_punto["tp"] * 1000  # m → mm
        df_punto["ro"] = df_punto["ro"] * 1000  # m → mm
        df_punto["sro"] = df_punto["sro"] * 1000  # m → mm

        # Velocidad del viento
        df_punto["wind_speed"] = np.sqrt(df_punto["u10"] ** 2 + df_punto["v10"] ** 2)

        dfs_era5.append(df_punto)
        print(f"    ✓ {codigo}")
    except Exception as e:
        print(f"    ✗ {codigo} falló: {e}")

df_era5 = pd.concat(dfs_era5, ignore_index=True)

# ═══════════════════════════════════════════════════════════════════════
# SST Niño 3.4 (UNA SOLA SERIE GLOBAL)
# ═══════════════════════════════════════════════════════════════════════

print("\n  Extrayendo SST Niño 3.4...")

PUNTO_NINO34 = {"lat": 5.0, "lon": -80.0}

ds_sst = xr.open_dataset(
    GRIB_PATH,
    engine="cfgrib",
    backend_kwargs={"filter_by_keys": {"shortName": "sst"}},
)

coords_to_drop = [c for c in DROP_COORDS if c in ds_sst.coords]
ds_sst = ds_sst.drop_vars(coords_to_drop)

ds_sst = ds_sst.assign_coords(time=ds_sst["time"].dt.floor("D"))

lats = ds_sst["latitude"].values
lons = ds_sst["longitude"].values

nearest_lat = lats[np.argmin(np.abs(lats - PUNTO_NINO34["lat"]))]
nearest_lon = lons[np.argmin(np.abs(lons - PUNTO_NINO34["lon"]))]

df_sst_nino = (
    ds_sst.sel(latitude=nearest_lat, longitude=nearest_lon)
    .to_dataframe()
    .reset_index()[["time", "sst"]]
    .rename(columns={"time": "Fecha", "sst": "sst_nino"})
)

df_sst_nino["sst_nino"] = df_sst_nino["sst_nino"] - 273.15
df_sst_nino["Fecha"] = pd.to_datetime(df_sst_nino["Fecha"])

print(f"  SST Niño 3.4: {df_sst_nino.shape}")
print(f"\n  ERA5 extraído: {df_era5.shape}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MERGE
# ═══════════════════════════════════════════════════════════════════════════════
paso(4, 4, "Uniendo datasets")

# Base: reservas
df = df_res.copy()

# Aportes por región
df = df.merge(df_ap_region, on=["Fecha", "RegionHidrologica"], how="left")

# ERA5 por embalse — solo el período que se solapa (2020-2024)
df = df.merge(df_era5, on=["Fecha", "CodigoEmbalse"], how="left")

df = df.merge(df_sst_nino, on="Fecha", how="left")

# Orden final de columnas
df = df[
    [
        "Fecha",
        "CodigoEmbalse",
        "RegionHidrologica",
        "reserva_pct",
        "aportes_masa",
        "media_historica_masa",
        "aportes_vs_media_pct",
        "t2m",
        "u10",
        "v10",
        "msl",
        "sst_nino",
        "tp",
        "ro",
        "sro",
        "swvl1",
        "wind_speed",
    ]
]

df = df.sort_values(["Fecha", "CodigoEmbalse"]).reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. GUARDAR
# ═══════════════════════════════════════════════════════════════════════════════
os.makedirs(OUTPUT_DIR, exist_ok=True)
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
