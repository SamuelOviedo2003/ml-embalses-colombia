# Proyecto ML — Riesgo de déficit energético en embalses colombianos

**Curso:** Aprendizaje de Máquina Aplicado — EAFIT  
**Profesor:** Marco Teran  
**Estudiante:** Samuel Oviedo Paz - Santiago Alberto Rozo Silva - Isis Catitza Amaya Arbelaez
**Metodología:** CRISP-DM

---

## Pregunta de investigación

> Dado que en 2026 se pronostica un Fenómeno del Niño en Colombia (época de sequía), y que el país depende mayoritariamente de hidroeléctricas, **¿en qué momentos los embalses del SIN alcanzarán niveles críticos con riesgo de déficit energético?**

**Tipo de tarea ML:** Regresión / serie de tiempo  
**Variable objetivo:** Porcentaje de volumen útil diario por embalse (`reserva_pct`)  
**Umbral de alerta histórico:** ~30% de capacidad útil del sistema

---

## Fuentes de datos

### Fuente 1 — SIMEM / XM (API oficial)
- **Qué es:** Sistema de Información del Mercado de Energía Mayorista de Colombia, operado por XM.
- **Acceso:** Librería `pydataxm` — [github.com/EquipoAnaliticaXM/API_XM](https://github.com/EquipoAnaliticaXM/API_XM)
- **Cobertura:** Desde 2000 hasta hoy, actualización diaria.

### Fuente 2 — NOAA / Kaggle (archivo local)
- **Qué es:** Dataset ENSO con múltiples índices climáticos: ONI, MEI.v2, SOI, Niño 3.4, entre otros.
- **Archivo:** `Datasets/ENSO.csv`
- **Fuente original:** Kaggle — "ENSO Related Standardized Monthly Climate Data (1950–2024)"
- **Cobertura:** 1950-01 — 2024-12, frecuencia mensual.

---

## Tablas descargadas

### `VolumenUtilPorcentaje` — Reservas hidráulicas (TARGET)

| Columna | Tipo | Descripción |
|---|---|---|
| `Fecha` | date | Fecha de la observación |
| `CodigoEmbalse` | str | Código del embalse (ej. `PENOL`, `ITUANGO`) |
| `RegionHidrologica` | str | Región geográfica (ej. `Antioquia`, `Centro`) |
| `VolumenUtilPorcentaje` | float | % volumen útil respecto a capacidad máxima (escala 0-1 en API, convertido a 0-100) |

**Nota:** Valores > 100 indican vertimientos (el embalse superó su nivel máximo). Son datos válidos, no errores.

---

### `AportesHidricosMasa` — Aportes hídricos diarios

| Columna | Tipo | Descripción |
|---|---|---|
| `Fecha` | date | Fecha de la observación |
| `CodigoSerieHidrologica` | str | Código de la serie (río/cuenca) |
| `RegionHidrologica` | str | Región geográfica |
| `AportesHidricosMasa` | float | Caudal diario total de la serie (m³) |
| `MediaHistoricaMasa` | float | Media histórica mensual para la misma serie (m³) |

**Transformación aplicada:** Se agrega por `(Fecha, RegionHidrologica)` sumando todas las series de la región, para que el join con embalses sea posible vía región.

---

### `ENSO.csv` — Índices climáticos ENSO

| Columna | Tipo | Descripción | Usada |
|---|---|---|---|
| `Date` | date | Primer día del mes (`YYYY-MM-DD`) | Sí (como `Fecha`) |
| `ONI` | float | Anomalía temperatura Pacífico central (°C) | Sí → `oni` |
| `MEI.v2` | float | Índice ENSO multivariado v2 (desde 1979) | Sí → `mei_v2` |
| `SOI` | float | Índice de Oscilación del Sur | No (en futuras versiones) |
| `Nino 3.4 SST Anomalies` | float | Anomalía en región 3.4 del Pacífico | No (en futuras versiones) |
| resto | — | Otros índices climáticos y estaciones | No |

**Interpretación ONI:**
- `> +0.5` por 5 meses consecutivos → **El Niño** (sequía en Colombia)
- Entre `-0.5` y `+0.5` → Neutro
- `< -0.5` por 5 meses consecutivos → **La Niña** (lluvias intensas)

**Transformación aplicada:** De mensual a diario usando `ffill`. Los meses 2025-01 a 2026-03 quedan como `NaN` (sin datos aún).

---

## Estrategia de unión (join)

```
VolumenUtilPorcentaje          AportesHidricosMasa (agregado por región)
(Fecha, CodigoEmbalse,    ←──→  (Fecha, RegionHidrologica)
 RegionHidrologica)             join por: Fecha + RegionHidrologica
         │
         │ join por: Fecha
         ▼
        ONI (expandido a diario)
```

**Resultado:** Una fila por `(Fecha, CodigoEmbalse)` con:

| Columna | Rol |
|---|---|
| `Fecha` | Identificador temporal |
| `CodigoEmbalse` | Identificador del embalse |
| `RegionHidrologica` | Identificador geográfico |
| `reserva_pct` | **TARGET** — % volumen útil (0-100) |
| `aportes_masa` | Feature — caudal total en la región (m³) |
| `media_historica_masa` | Feature — referencia histórica para el período (m³) |
| `aportes_vs_media_pct` | Feature — % aportes vs media histórica (< 100 = sequía) |
| `oni` | Feature — señal climática El Niño/La Niña (NaN para 2025–2026) |
| `mei_v2` | Feature — índice ENSO multivariado, más sensible que ONI (NaN para 2025–2026) |

---

## Scripts

| Script | Qué hace |
|---|---|
| `explorar_datos.py` | Descarga una semana de muestra de cada fuente y muestra `.head()` |
| `construir_dataset.py` | Descarga el rango completo (2000–2026), une y guarda `Datasets/dataset_final.csv` |

---

## Estructura del repositorio

```
proyecto/
  README.md                          ← este archivo
  CLAUDE.md                          ← guía para Claude Code
  glosario.md                        ← definición de términos del dominio
  explorar_datos.py                  ← exploración rápida de fuentes
  construir_dataset.py               ← construcción del dataset final
  API_XM/                            ← librería pydataxm (git clone)
  Datasets/
    ENSO.csv                         ← índices climáticos ENSO 1950-2024 (Kaggle/NOAA)
    dataset_final.csv                ← generado por construir_dataset.py
  notebooks/                         ← (por crear) Jupyter notebooks del proyecto
  report/                            ← (por crear) reportes PDF
  referencias.txt                    ← URLs de fuentes
```

---

## Reproducibilidad

Para reconstruir el dataset desde cero:

```bash
# 1. Clonar la librería XM (ya hecho)
git clone https://github.com/EquipoAnaliticaXM/API_XM

# 2. Instalar dependencias
pip install ./API_XM

# 3. Construir el dataset (tarda ~20 min)
python3 construir_dataset.py
```

El archivo `ENSO.csv` ya está incluido en el repositorio (`Datasets/ENSO.csv`).
