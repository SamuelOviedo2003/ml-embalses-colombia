# Datacard — Dataset de Reservas Hidráulicas en Colombia

---

## Fuente de los datos

El dataset fue construido a partir de la combinación de dos fuentes de datos externas:

- **XM — Mercado de Energía Mayorista colombiano:** datos operativos diarios de reservas hidráulicas y aportes hídricos de los embalses del Sistema Interconectado Nacional (SIN), disponibles a través de la plataforma SIMEM.
- **ECMWF — Climate Data Store (ERA5):** reanálisis climático global publicado por el Centro Europeo de Predicciones Meteorológicas a Plazo Medio, con resolución espacial de 0.25° (~31 km) y cobertura horaria.

El proceso de integración consistió en cruzar ambas fuentes por fecha, y para los datos ERA5, extraer el punto de grilla geográficamente más cercano a las coordenadas de cada embalse (latitud, longitud), de modo que cada registro del dataset corresponde a un embalse específico en una fecha específica.

---

## Tamaño

| Etapa                        | Filas  | Columnas |
| ---------------------------- | ------ | -------- |
| Antes del preprocesamiento   | 99,838 | 17       |
| Después del preprocesamiento | 99,838 | —        |

---

## Variables

### Target

| Variable      | Descripción                                   | Unidad      |
| ------------- | --------------------------------------------- | ----------- |
| `reserva_pct` | Porcentaje de volumen útil diario del embalse | % (0 – 100) |

### Features

| Variable               | Descripción                                                    | Unidad | Fuente   |
| ---------------------- | -------------------------------------------------------------- | ------ | -------- |
| `aportes_masa`         | Caudal hídrico total diario en la región                       | m³     | XM       |
| `media_historica_masa` | Media histórica del caudal para el mismo período               | m³     | XM       |
| `aportes_vs_media_pct` | Relación entre aportes actuales y media histórica              | %      | XM       |
| `t2m`                  | Temperatura del aire a 2 m de altura                           | °C     | ERA5     |
| `u10`                  | Componente zonal del viento a 10 m (este–oeste)                | m/s    | ERA5     |
| `v10`                  | Componente meridional del viento a 10 m (norte–sur)            | m/s    | ERA5     |
| `msl`                  | Presión atmosférica al nivel del mar                           | hPa    | ERA5     |
| `sst`                  | Temperatura superficial del mar                                | °C     | ERA5     |
| `tp`                   | Precipitación total acumulada                                  | mm     | ERA5     |
| `ro`                   | Escorrentía total                                              | mm     | ERA5     |
| `sro`                  | Escorrentía superficial                                        | mm     | ERA5     |
| `swvl1`                | Humedad volumétrica del suelo — capa 1 (0–7 cm)                | m³/m³  | ERA5     |
| `wind_speed`           | Velocidad escalar del viento (calculada a partir de u10 y v10) | m/s    | Derivada |

---

## Tipo de tarea

El problema corresponde a una tarea de **predicción en series de tiempo (Time Series Forecasting)**, específicamente una regresión temporal sobre una variable continua (`reserva_pct`). Dado que la relación entre las variables climáticas y el nivel de los embalses es no lineal y dependiente del tiempo, se enmarca como una **regresión temporal no lineal**.

---

## Limitaciones y riesgos potenciales

- **Ausencia de un dataset preexistente:** no existe un conjunto de datos público que integre directamente variables climáticas con niveles de embalses colombianos. Fue necesario construir el dataset desde cero combinando fuentes heterogéneas, lo que introduce potenciales inconsistencias.

- **Resolución temporal fija:** ERA5 ofrece datos cada hora (24 registros por día), pero para garantizar consistencia con los datos diarios de XM se seleccionó una única hora representativa del día (17:00 UTC). Esto implica que las variables climáticas no reflejan el promedio diario sino un instante específico.

- **Aproximación geográfica de los embalses:** ERA5 tiene una resolución de 0.25° (~31 km), por lo que la ubicación de cada embalse se aproximó al punto de grilla más cercano disponible. Esta aproximación puede no representar con precisión las condiciones microclimáticas de la cuenca hidrográfica de cada embalse.

- **Tratamiento de la variable `sst`:** la temperatura superficial del mar (SST) es nula en píxeles terrestres dentro de ERA5, por lo que asignar este valor al punto geográfico de cada embalse resulta en datos completamente faltantes. Como alternativa, se extrajo la SST de un punto oceánico fijo representativo de la señal ENSO (región Niño 3.4). Sin embargo, aplicar un único valor oceánico de forma uniforme a todos los embalses representa una simplificación.
