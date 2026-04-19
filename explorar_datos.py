"""
Exploración inicial de fuentes de datos del proyecto.
Objetivo: hacer .head() e info de cada dataset antes de usarlos en el notebook.
Módulo: pydatasimem (requests síncrono — compatible con Python 3.14)

Códigos de variables SIMEM confirmados:
  TARGET  : VolumenUtilPorcentaje  — % volumen útil diario por embalse
  FEATURES: AportesHidricosMasa   — caudal afluente por serie hidrológica (m3/s)
            DdaReal               — demanda real del SIN (GWh)
            GReal                 — generación real por planta (GWh, horaria)
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'API_XM'))
from pydataxm.pydatasimem import VariableSIMEM

# Rango corto solo para explorar — no descargar años completos aún
FECHA_INICIO = "2023-01-01"
FECHA_FIN    = "2023-01-15"

def explorar(nombre, df):
    print(f"\n{'='*60}")
    print(f"  {nombre}")
    print(f"{'='*60}")
    print(f"Filas x Columnas: {df.shape}")
    print(f"\n--- Tipos de datos ---")
    print(df.dtypes)
    print(f"\n--- Primeras filas ---")
    print(df.head(10).to_string())


# ── 1. TARGET: % Volumen Útil Diario por Embalse ─────────────────────────────
print("\n>>> [1/5] VolumenUtilPorcentaje — % reserva diaria por embalse...")
df_reservas = VariableSIMEM(
    cod_variable="VolumenUtilPorcentaje",
    start_date=FECHA_INICIO,
    end_date=FECHA_FIN
).get_data()
explorar("TARGET — % Volumen Útil Diario por Embalse", df_reservas)


# ── 2. FEATURE: Aportes Caudal ───────────────────────────────────────────────
print("\n>>> [2/5] AportesHidricosMasa — caudal afluente por serie hidrológica...")
df_aportes = VariableSIMEM(
    cod_variable="AportesHidricosMasa",
    start_date=FECHA_INICIO,
    end_date=FECHA_FIN
).get_data()
explorar("FEATURE — Aportes Caudal por Serie Hidrológica (m3/s)", df_aportes)


# ── 3. FEATURE: Demanda Real del SIN ─────────────────────────────────────────
print("\n>>> [3/5] DdaReal — demanda real del SIN...")
df_demanda = VariableSIMEM(
    cod_variable="DdaReal",
    start_date=FECHA_INICIO,
    end_date=FECHA_FIN
).get_data()
explorar("FEATURE — Demanda Real del SIN (GWh)", df_demanda)


# ── 4. FEATURE: Generación Real por Planta ───────────────────────────────────
print("\n>>> [4/5] GReal — generación real por planta (horaria)...")
df_generacion = VariableSIMEM(
    cod_variable="GReal",
    start_date=FECHA_INICIO,
    end_date=FECHA_FIN
).get_data()
explorar("FEATURE — Generación Real por Planta (horaria → agregar a diaria)", df_generacion)


# ── 5. ONI — archivo local ────────────────────────────────────────────────────
print("\n>>> [5/5] ONI — índice climático NOAA (archivo local)...")
ruta_oni = os.path.join(os.path.dirname(__file__), "Datasets", "Monthly Oceanic Nino Index (ONI) - Long.csv")
df_oni = pd.read_csv(ruta_oni)
explorar("FEATURE — Índice ONI mensual (NOAA)", df_oni)


print("\n\n✓ Exploración completa.")
