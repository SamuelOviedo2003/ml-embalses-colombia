# Proyecto ML: Riesgo de déficit energético en embalses colombianos

**Curso:** Aprendizaje de Máquina Aplicado, EAFIT  
**Profesor:** Marco Teran  
**Equipo:** Samuel Oviedo Paz, Santiago Alberto Rozo Silva, Isis Catitza Amaya Arbelaez  
**Metodología:** CRISP-DM

---

## Problema planteado

Dado el pronóstico de un evento fuerte del fenómeno de El Niño en Colombia durante 2026 (caracterizado por una disminución significativa de las precipitaciones y aumento de temperaturas), se busca identificar en qué momentos del año los embalses del Sistema Interconectado Nacional (SIN) alcanzarán niveles críticos que puedan comprometer la seguridad energética del país.

Esto implica analizar la evolución temporal de los niveles de almacenamiento hídrico frente a escenarios de sequía prolongada, con el fin de anticipar posibles déficits en la generación hidroeléctrica.

## Motivación

Colombia depende en gran medida de la generación hidroeléctrica para su suministro de energía, lo que la hace altamente vulnerable a eventos climáticos como El Niño.

Las alertas recientes indican que:

- Existe hasta un **90% de probabilidad** de que El Niño se consolide en septiembre de 2026, con impactos crecientes desde mitad de año.
- El fenómeno está asociado con reducción de lluvias y sequías, afectando directamente los niveles de los embalses.
- Ya se han evidenciado descensos acelerados en los niveles de embalses (reducciones de hasta ~17 puntos porcentuales en pocos meses) y riesgo de racionamiento, incluso antes del pico del fenómeno.

Anticipar los momentos críticos permite optimizar decisiones como: activación de plantas térmicas, gestión de la demanda, y planeación de importaciones de energía o gas.

## Contexto

El Niño en Colombia suele provocar déficits de precipitación especialmente en las regiones Andina, Caribe y Pacífica. Para 2026, el fenómeno podría iniciar entre mayo y julio, intensificándose progresivamente con intensidad moderada a fuerte hacia el último trimestre. Históricamente, eventos similares han provocado crisis energéticas (como el apagón de los años 90), lo que llevó a diversificar parcialmente la matriz con generación térmica.

---

## Pregunta de investigación

> Dado el Fenómeno del Niño 2026, **¿en qué momentos los embalses colombianos del SIN alcanzarán niveles críticos con riesgo de déficit energético?**

**Tipo de tarea ML:** Regresión / serie de tiempo  
**Variable objetivo:** `reserva_pct`, porcentaje de volumen útil diario por embalse (0-100%)  
**Umbral de alerta histórico:** ~30% de capacidad útil del sistema

---

## Fuentes de datos

### Fuente 1: SIMEM / XM (API oficial)
- **Qué es:** Sistema de Información del Mercado de Energía Mayorista de Colombia, operado por XM.
- **Acceso:** Librería `pydataxm` ([github.com/EquipoAnaliticaXM/API_XM](https://github.com/EquipoAnaliticaXM/API_XM))
- **Variables usadas:** `VolumenUtilPorcentaje` (TARGET), `AportesHidricosMasa` (features hidrológicas)
- **Cobertura:** Desde 2000 hasta hoy, actualización diaria.

### Fuente 2: ERA5 / Copernicus (archivo local `.grib`)
- **Qué es:** Reanálisis climático global de ECMWF a resolución 0.25°, distribuido por el Copernicus Climate Change Service.
- **Archivo:** `Datasets/combinado.grib` (no versionado en git por tamaño)
- **Variables extraídas:** `t2m`, `u10`, `v10`, `msl`, `tp`, `ro`, `sro`, `swvl1`, `sst` (Niño 3.4)
- **Cobertura:** 2013-01-01 a 2024-12-31, frecuencia diaria.
- **Documentación:** [ERA5 data documentation](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)

---

## Descripción de variables del dataset

### TARGET

| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `reserva_pct` | % | Porcentaje del volumen útil del embalse respecto a su capacidad total (0-100). Valores >100 indican vertimiento (son válidos). Umbral crítico histórico: ~30%. |

### Features hidrológicas (SIMEM/XM)

| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `aportes_masa` | m³ | Volumen total de agua que entra al embalse (afluencias desde lluvia, escorrentía y ríos). Agregado por región hidrológica. |
| `media_historica_masa` | m³ | Promedio histórico de aportes para el mismo período. Sirve como línea base de referencia. |
| `aportes_vs_media_pct` | % | `aportes_masa / media_historica_masa x 100`. Valor menor a 100 indica sequía; mayor a 100 indica año húmedo. |

### Features meteorológicas (ERA5 / Copernicus)

| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `t2m` | °C | Temperatura del aire a 2m. Afecta evaporación del embalse y demanda energética. |
| `u10` | m/s | Componente zonal del viento a 10m (este = positivo). |
| `v10` | m/s | Componente meridional del viento a 10m (norte = positivo). |
| `wind_speed` | m/s | Magnitud del viento: `sqrt(u10^2 + v10^2)`. |
| `msl` | hPa | Presión al nivel del mar. Baja presión indica mayor probabilidad de lluvia; alta presión indica condiciones secas. |
| `tp` | mm | Precipitación total acumulada. Variable clave para recarga de embalses. |
| `ro` | mm | Escorrentía total (sobre y bajo la superficie). Puente entre lluvia y aporte al embalse. |
| `sro` | mm | Escorrentía superficial. Responde rápido a lluvias intensas. |
| `swvl1` | m³/m³ | Humedad volumétrica del suelo, capa superficial. Influye en capacidad de generar escorrentía. |

### Feature oceánica (ERA5, señal El Niño)

| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `sst_nino` | °C | Temperatura superficial del mar en la región Niño 3.4 (5°N, 80°W). Serie global única. Anomalías positivas indican El Niño, lo que se traduce en menor lluvia y descenso de embalses. |

---

## Dataset final: `Datasets/dataset_final.csv`

~99,000 filas. Una fila por `(Fecha, CodigoEmbalse)`.  
**Período:** 2013-01-01 a 2024-12-31. **Embalses:** 24 del SIN.

### Estrategia de unión

El dataset se construye en cuatro pasos:

1. **Base:** `VolumenUtilPorcentaje` (SIMEM) por `(Fecha, CodigoEmbalse)`.
2. **Join hidrológico:** `AportesHidricosMasa` (SIMEM) agregado por `(Fecha, RegionHidrologica)`, unido a la base por `Fecha + RegionHidrologica` (los aportes no existen a nivel de embalse individual, solo por región).
3. **Join ERA5:** variables climáticas extraídas del punto de grilla 0.25° más cercano a cada embalse, unidas por `Fecha + CodigoEmbalse`.
4. **Join SST:** temperatura superficial del mar en Niño 3.4 (serie global única), unida por `Fecha`.

Las variables ERA5 cubren solo 2013-2024 (límite del archivo `.grib` local); fuera de ese rango quedan como `NaN`.

---

## Scripts

| Script | Descripción |
|--------|-------------|
| `construir_dataset.py` | Pipeline completo: descarga SIMEM, carga ERA5 desde `.grib`, une y guarda `Datasets/dataset_final.csv`. Tarda aproximadamente 20 minutos. |

---

## Estructura del repositorio

```
ml-embalses-colombia/
  README.md                      este archivo
  glosario.md                    definición de términos del dominio
  referencias.txt                URLs de fuentes
  construir_dataset.py           construcción del dataset final
  Datasets/
    combinado.grib               ERA5 local (no versionado en git)
    dataset_final.csv            generado por construir_dataset.py
  ML - Embalses_Untitled1.ipynb  EDA
```


