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
                sst_nino12_proxy     — proxy SST Niño 1+2 parcial (°C)
                oni_anom             — Oceanic Niño Index oficial NOAA/CPC (°C)
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
import gc
from urllib.request import urlretrieve

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "API_XM"))
from pydataxm.pydatasimem import VariableSIMEM

# ── Parámetros ────────────────────────────────────────────────────────────────
START_DATE = "2013-01-01"
END_DATE = "2024-12-31"

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "Datasets")
GRIB_PATH = os.path.join(
    OUTPUT_DIR, "copernicus_completo.grib"
)  # ← ajusta si el .grib está en otra ruta
FOUR_HOURS_DIR = os.path.join(BASE_DIR, "FourHours")
GRIB_PART_PATHS = [
    os.path.join(FOUR_HOURS_DIR, "2013_2017.grib"),
    os.path.join(FOUR_HOURS_DIR, "2018_2022.grib"),
    os.path.join(FOUR_HOURS_DIR, "2023_2024.grib"),
]
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
ONI_PATH = os.path.join(OUTPUT_DIR, "oni_noaa_cpc.ascii.txt")
ERA5_DIARIO_PATH = os.path.join(OUTPUT_DIR, "era5_diario_embalses.csv")
NINO12_PROXY_PATH = os.path.join(OUTPUT_DIR, "sst_nino12_proxy_diario.csv")
REQUIRED_ERA5_COLUMNS = [
    "Fecha",
    "CodigoEmbalse",
    "t2m",
    "u10",
    "v10",
    "msl",
    "tp",
    "ro",
    "sro",
    "swvl1",
    "wind_speed",
]
REQUIRED_NINO12_COLUMNS = ["Fecha", "sst_nino12_proxy"]

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

DROP_COORDS = ["number", "surface", "depthBelowLandLayer"]
SEASON_CENTER_MONTH = {
    "DJF": 1,
    "JFM": 2,
    "FMA": 3,
    "MAM": 4,
    "AMJ": 5,
    "MJJ": 6,
    "JJA": 7,
    "JAS": 8,
    "ASO": 9,
    "SON": 10,
    "OND": 11,
    "NDJ": 12,
}


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


def get_grib_sources():
    """Usa los GRIB partidos si existen; si no, usa el GRIB combinado."""
    grib_parts = [path for path in GRIB_PART_PATHS if os.path.exists(path)]
    if grib_parts:
        return grib_parts
    return [GRIB_PATH]


def open_grib_variable(grib_path, var_name, filter_by_keys):
    """Abre una variable del GRIB sin forzar merge entre ejes temporales distintos."""
    ds_var = xr.open_dataset(
        grib_path,
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": filter_by_keys},
    )
    coords_to_drop = [c for c in DROP_COORDS if c in ds_var.coords]
    ds_var = ds_var.drop_vars(coords_to_drop)

    if var_name not in ds_var.data_vars:
        data_vars = list(ds_var.data_vars)
        if len(data_vars) != 1:
            raise ValueError(f"{var_name}: variables encontradas {data_vars}")
        ds_var = ds_var.rename({data_vars[0]: var_name})

    return ds_var


def daily_points_mean(ds_var, var_name):
    """Extrae todos los embalses a la vez y promedia las observaciones por día."""
    codigos = list(COORDENADAS_EMBALSES.keys())
    lats = xr.DataArray(
        [COORDENADAS_EMBALSES[codigo]["lat"] for codigo in codigos],
        dims="point",
        coords={"CodigoEmbalse": ("point", codigos)},
    )
    lons = xr.DataArray(
        [COORDENADAS_EMBALSES[codigo]["lon"] for codigo in codigos],
        dims="point",
        coords={"CodigoEmbalse": ("point", codigos)},
    )

    ds_puntos = ds_var[[var_name]].sel(latitude=lats, longitude=lons, method="nearest")
    df_puntos = ds_puntos.to_dataframe().reset_index()
    time_col = "valid_time" if "valid_time" in df_puntos.columns else "time"

    df_puntos["Fecha"] = pd.to_datetime(df_puntos[time_col]).dt.floor("D")
    return df_puntos.groupby(["Fecha", "CodigoEmbalse"], as_index=False)[
        var_name
    ].mean()


def daily_area_mean(ds_var, var_name, lat_min, lat_max, lon_min, lon_max):
    """Promedia una caja espacial y luego promedia las observaciones por día."""
    lats = ds_var["latitude"].values
    lons = ds_var["longitude"].values
    lat_slice = (
        slice(lat_max, lat_min) if lats[0] > lats[-1] else slice(lat_min, lat_max)
    )
    lon_slice = (
        slice(lon_min, lon_max) if lons[0] < lons[-1] else slice(lon_max, lon_min)
    )

    ds_area = ds_var.sel(latitude=lat_slice, longitude=lon_slice)
    ds_area = ds_area[[var_name]].mean(dim=["latitude", "longitude"], skipna=True)
    df_area = ds_area.to_dataframe().reset_index()
    time_col = "valid_time" if "valid_time" in df_area.columns else "time"

    df_area["Fecha"] = pd.to_datetime(df_area[time_col]).dt.floor("D")
    return df_area.groupby("Fecha", as_index=False)[var_name].mean()


def convertir_unidades_era5(df_era5):
    """Convierte unidades ERA5 después del promedio diario."""
    for col in ["t2m", "sst_nino12_proxy"]:
        if col in df_era5:
            df_era5[col] = df_era5[col] - 273.15
    if "msl" in df_era5:
        df_era5["msl"] = df_era5["msl"] / 100
    for col in ["tp", "ro", "sro"]:
        if col in df_era5:
            df_era5[col] = df_era5[col] * 1000
    return df_era5


def leer_cache_csv(path, required_columns, min_rows=None):
    """Lee un cache CSV solo si existe y contiene las columnas esperadas."""
    if not os.path.exists(path):
        return None

    try:
        df_cache = pd.read_csv(path, parse_dates=["Fecha"])
    except Exception as e:
        print(f"  Cache inválido, se reconstruirá: {path} ({e})")
        return None

    missing = set(required_columns) - set(df_cache.columns)
    if missing:
        print(f"  Cache incompleto, se reconstruirá: {path} faltan {sorted(missing)}")
        return None

    if min_rows is not None and len(df_cache) < min_rows:
        print(
            f"  Cache incompleto, se reconstruirá: {path} "
            f"filas {len(df_cache):,} < {min_rows:,}"
        )
        return None

    return df_cache


def guardar_cache_csv(df_cache, path):
    """Escribe cache de forma atómica para evitar archivos parciales si se interrumpe."""
    tmp_path = f"{path}.tmp"
    df_cache.to_csv(tmp_path, index=False)
    os.replace(tmp_path, path)


def cargar_oni_diario():
    """Descarga ONI oficial NOAA/CPC y repite cada valor para los días de su mes."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(ONI_PATH):
        print(f"  Descargando ONI desde NOAA/CPC: {ONI_URL}")
        urlretrieve(ONI_URL, ONI_PATH)
    else:
        print(f"  Usando ONI local: {ONI_PATH}")

    df_oni = pd.read_csv(ONI_PATH, sep=r"\s+")
    df_oni["month"] = df_oni["SEAS"].map(SEASON_CENTER_MONTH)
    df_oni = df_oni.dropna(subset=["month"]).copy()
    df_oni["Fecha"] = pd.to_datetime(
        {
            "year": df_oni["YR"].astype(int),
            "month": df_oni["month"].astype(int),
            "day": 1,
        }
    )
    df_oni = df_oni.rename(columns={"ANOM": "oni_anom"})
    df_oni = df_oni[["Fecha", "oni_anom"]].sort_values("Fecha")

    fechas_diarias = pd.DataFrame(
        {"Fecha": pd.date_range(START_DATE, END_DATE, freq="D")}
    )
    fechas_diarias["mes_oni"] = (
        fechas_diarias["Fecha"].dt.to_period("M").dt.to_timestamp()
    )
    df_oni_diario = fechas_diarias.merge(
        df_oni, left_on="mes_oni", right_on="Fecha", how="left", suffixes=("", "_oni")
    )
    df_oni_diario = df_oni_diario[["Fecha", "oni_anom"]]
    df_oni_diario["oni_anom"] = df_oni_diario["oni_anom"].ffill().bfill()
    return df_oni_diario


def cargar_era5_diario(VARIABLES_GRIB):
    """Carga el cache diario ERA5 o lo construye leyendo una variable GRIB a la vez."""
    min_rows_era5 = int(
        len(pd.date_range(START_DATE, END_DATE, freq="D"))
        * len(COORDENADAS_EMBALSES)
        * 0.95
    )
    df_cache = leer_cache_csv(
        ERA5_DIARIO_PATH, REQUIRED_ERA5_COLUMNS, min_rows=min_rows_era5
    )
    if df_cache is not None:
        print(f"  Usando ERA5 diario cacheado: {ERA5_DIARIO_PATH}")
        return df_cache

    grib_sources = get_grib_sources()
    print(f"  Fuentes GRIB a procesar: {len(grib_sources)}")
    df_era5 = None

    for var_name, keys in VARIABLES_GRIB.items():
        partes_var = []
        try:
            for grib_path in grib_sources:
                ds_var = None
                try:
                    ds_var = open_grib_variable(grib_path, var_name, keys)
                    print(
                        f"  ✓ {var_name} en {os.path.basename(grib_path)}: {dict(ds_var.sizes)}"
                    )
                    partes_var.append(daily_points_mean(ds_var, var_name))
                finally:
                    if ds_var is not None:
                        ds_var.close()
                    gc.collect()

            df_var = pd.concat(partes_var, ignore_index=True)
            df_var = df_var.groupby(["Fecha", "CodigoEmbalse"], as_index=False)[
                var_name
            ].mean()

            if df_era5 is None:
                df_era5 = df_var
            else:
                df_era5 = df_era5.merge(
                    df_var, on=["Fecha", "CodigoEmbalse"], how="outer"
                )
        except Exception as e:
            print(f"  ✗ {var_name} falló: {e}")
            gc.collect()

    if df_era5 is None or df_era5.empty:
        raise RuntimeError("No se pudo construir ERA5 diario desde el GRIB.")

    df_era5 = convertir_unidades_era5(df_era5)
    if {"u10", "v10"}.issubset(df_era5.columns):
        df_era5["wind_speed"] = np.sqrt(df_era5["u10"] ** 2 + df_era5["v10"] ** 2)
    df_era5 = df_era5.sort_values(["Fecha", "CodigoEmbalse"]).reset_index(drop=True)
    guardar_cache_csv(df_era5, ERA5_DIARIO_PATH)
    print(f"  Cache ERA5 diario guardado en: {ERA5_DIARIO_PATH}")
    return df_era5


def cargar_sst_nino12_proxy_diario():
    """Carga el cache del proxy Niño 1+2 o lo construye desde la SST del GRIB."""
    min_rows_nino12 = int(len(pd.date_range(START_DATE, END_DATE, freq="D")) * 0.95)
    df_cache = leer_cache_csv(
        NINO12_PROXY_PATH, REQUIRED_NINO12_COLUMNS, min_rows=min_rows_nino12
    )
    if df_cache is not None:
        print(f"  Usando SST Niño 1+2 proxy cacheado: {NINO12_PROXY_PATH}")
        return df_cache

    partes_sst = []
    for grib_path in get_grib_sources():
        ds_sst = None
        try:
            ds_sst = open_grib_variable(
                grib_path, "sst_nino12_proxy", {"shortName": "sst"}
            )
            partes_sst.append(
                daily_area_mean(
                    ds_sst,
                    "sst_nino12_proxy",
                    lat_min=-5,
                    lat_max=0,
                    lon_min=-85,
                    lon_max=-80,
                )
            )
        finally:
            if ds_sst is not None:
                ds_sst.close()
            gc.collect()

    df_sst_nino12 = pd.concat(partes_sst, ignore_index=True)
    df_sst_nino12 = df_sst_nino12.groupby("Fecha", as_index=False)[
        "sst_nino12_proxy"
    ].mean()

    df_sst_nino12 = convertir_unidades_era5(df_sst_nino12)
    df_sst_nino12["Fecha"] = pd.to_datetime(df_sst_nino12["Fecha"])
    df_sst_nino12 = df_sst_nino12.sort_values("Fecha").reset_index(drop=True)
    guardar_cache_csv(df_sst_nino12, NINO12_PROXY_PATH)
    print(f"  Cache SST Niño 1+2 proxy guardado en: {NINO12_PROXY_PATH}")
    return df_sst_nino12


# ═══════════════════════════════════════════════════════════════════════════════
# 1. RESERVAS — TARGET
# ═══════════════════════════════════════════════════════════════════════════════
paso(1, 5, "Descargando reservas hidráulicas (VolumenUtilPorcentaje)")

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
paso(2, 5, "Descargando aportes hídricos (AportesHidricosMasa)")

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
paso(3, 5, f"Cargando variables ERA5 desde {GRIB_PATH}")

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

df_era5 = cargar_era5_diario(VARIABLES_GRIB)
print(f"\n  ERA5 diario extraído: {df_era5.shape}")

# ═══════════════════════════════════════════════════════════════════════
# ENSO: ONI oficial NOAA/CPC y proxy Niño 1+2 desde SST regional
# ═══════════════════════════════════════════════════════════════════════
paso(4, 5, "Construyendo features ENSO")

df_oni_diario = cargar_oni_diario()
print(f"  ONI diario: {df_oni_diario.shape}")

print("\n  Extrayendo proxy SST Niño 1+2 parcial (80W-85W, 0-5S)...")
df_sst_nino12 = cargar_sst_nino12_proxy_diario()
print(f"  SST Niño 1+2 proxy diario: {df_sst_nino12.shape}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MERGE
# ═══════════════════════════════════════════════════════════════════════════════
paso(5, 5, "Uniendo datasets")

# Base: reservas
df = df_res.copy()

# Aportes por región
df = df.merge(df_ap_region, on=["Fecha", "RegionHidrologica"], how="left")

# ERA5 diario por embalse
df = df.merge(df_era5, on=["Fecha", "CodigoEmbalse"], how="left")

df = df.merge(df_sst_nino12, on="Fecha", how="left")
df = df.merge(df_oni_diario, on="Fecha", how="left")

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
        "sst_nino12_proxy",
        "oni_anom",
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
