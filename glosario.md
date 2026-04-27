# Glosario del proyecto — Embalses y sistema eléctrico colombiano

---

## Sistema eléctrico

**SIN — Sistema Interconectado Nacional**
Red eléctrica que conecta la generación y el consumo de energía en la mayor parte del territorio colombiano. Está operado y supervisado por XM. La mayoría de embalses del país hacen parte del SIN.

**XM**
Empresa filial de ISA encargada de operar el SIN y administrar el mercado de energía mayorista en Colombia. Es la principal fuente de datos históricos de reservas, aportes, vertimientos y generación.

**SIMEM — Sistema de Información del Mercado de Energía Mayorista**
Portal oficial de XM que centraliza datos operativos del sistema eléctrico colombiano. Fuente de `VolumenUtilPorcentaje` (TARGET) y `AportesHidricosMasa`. Accesible vía la librería `pydataxm`.

**Capacidad útil total del sistema**
Suma del volumen útil de todos los embalses del SIN. Es el denominador con el que se calcula el porcentaje de reservas del sistema.

**Generación hidroeléctrica**
Producción de electricidad a partir del agua turbinada en una central hidráulica. Consume el agua almacenada en el embalse (reduce el nivel).

**Demanda eléctrica**
Cantidad de energía que consume el sistema en un período dado (GWh/día). A mayor demanda, mayor presión sobre los embalses para generar.

---

## Embalses y agua

**Embalse**
Depósito artificial de agua creado represando un río. En Colombia los más relevantes para el SIN son: Guatapé (Antioquia), Betania (Huila), Calima (Valle), Salvajina, La Miel, entre otros.

**Volumen total del embalse (Mm³)**
Capacidad física máxima del embalse. Incluye el volumen muerto (que no puede usarse).

**Volumen útil (Mm³)**
Agua que realmente puede aprovecharse para generar electricidad. Es el volumen entre el nivel mínimo técnico y el nivel máximo. Es la variable más importante para el proyecto.

**Volumen muerto**
Parte del agua almacenada que no puede turbinarse por estar por debajo de las estructuras de captación. No es energéticamente aprovechable.

**Nivel máximo físico**
Nivel al que el embalse está 100% lleno. Si se supera, el agua debe vertirse obligatoriamente para evitar daños en la presa.

**Nivel mínimo técnico**
Nivel por debajo del cual el embalse no puede operar las turbinas. Si el embalse llega a este punto, la central queda fuera de servicio.

---

## Las variables clave del dataset

**reserva_pct — TARGET**
Agua almacenada en la zona útil de los embalses, expresada como porcentaje de la capacidad útil total. Rango 0-100; valores >100 indican vertimiento (válidos). El seguimiento diario en % es la métrica oficial que usa XM para alertas.
- Umbral crítico histórico: aproximadamente **30%** activa alertas oficiales.

**aportes_masa**
Volumen total de agua que llega a los embalses desde los ríos (lluvia + escorrentía de cuencas). Se expresa en m³/día. Es el "ingreso" del sistema. En el dataset se agrega por región hidrológica.

**media_historica_masa**
Promedio histórico de aportes para el mismo mes/período. Sirve de línea base para detectar anomalías.

**aportes_vs_media_pct**
`aportes_masa / media_historica_masa × 100`. Si <100 hay déficit hídrico; si >100 es año húmedo. Durante El Niño cae consistentemente por debajo de 100.

**Vertimientos**
Agua que se evacua del embalse cuando supera su nivel máximo físico. Es agua que se "pierde" sin generar electricidad. Durante El Niño los vertimientos son prácticamente cero.

---

## Variables meteorológicas (ERA5 / Copernicus)

**ERA5**
Reanálisis climático global producido por el ECMWF (European Centre for Medium-Range Weather Forecasts) y distribuido por el Copernicus Climate Change Service. Resolución 0.25° (~28 km), frecuencia horaria, disponible desde 1940. En el proyecto se usa la resolución diaria. Documentación: https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation

**t2m — Temperatura a 2 metros (°C)**
Temperatura del aire cerca de la superficie. Afecta la evaporación del embalse y la demanda energética (más calor = más consumo eléctrico).

**u10 — Viento zonal a 10m (m/s)**
Componente este-oeste del viento. Positivo: hacia el este. Negativo: hacia el oeste.

**v10 — Viento meridional a 10m (m/s)**
Componente norte-sur del viento. Positivo: hacia el norte. Negativo: hacia el sur.

**wind_speed — Velocidad del viento (m/s)**
Magnitud del vector viento: `√(u10² + v10²)`. Impacta evaporación y dinámica atmosférica.

**msl — Presión al nivel del mar (hPa)**
Indica sistemas de alta o baja presión. Baja presión → mayor probabilidad de lluvia. Alta presión → condiciones secas.

**tp — Precipitación total (mm)**
Lluvia acumulada. Variable clave para recarga de embalses y generación de aportes.

**ro — Escorrentía total (mm)**
Agua que fluye sobre y bajo el suelo hacia los ríos. Es el puente entre la precipitación y los aportes al embalse.

**sro — Escorrentía superficial (mm)**
Fracción de la escorrentía que fluye directamente sobre la superficie. Responde rápido a lluvias intensas.

**swvl1 — Humedad volumétrica del suelo, capa 1 (m³/m³)**
Contenido de agua en la capa superficial del suelo. Influye en la capacidad de generar escorrentía y es señal de sequías prolongadas.

---

## Variable oceánica — señal El Niño

**sst_nino — Temperatura superficial del mar en región Niño 3.4 (°C)**
Temperatura del océano Pacífico ecuatorial en la región Niño 3.4 (aprox. 5°N, 80°W). Es el predictor climático clave: anomalías positivas indican El Niño → menor lluvia sobre Colombia → embalses bajan. En el dataset es una sola serie global extraída del archivo ERA5.

---

## Hidrología y clima

**Cuenca hidrográfica**
Área geográfica cuyas aguas superficiales drenan hacia un mismo río o embalse. Los aportes al embalse dependen de la lluvia que cae en su cuenca.

**Región hidrológica**
Agrupación geográfica de cuencas con comportamiento hidrológico similar. XM divide Colombia en varias regiones (Caribe, Andina, Pacífico, Orinoquía, Amazonía). Es la clave de join entre aportes y reservas en el dataset.

**Caudal (m³/s)**
Volumen de agua que pasa por un punto de un río por unidad de tiempo. Es la unidad base de los aportes.

**Media histórica mensual**
Promedio del caudal (o nivel) para un mes específico calculado sobre todos los años históricos disponibles. Sirve como referencia para saber si el año actual es seco o húmedo.

---

## Fenómeno del Niño / ENSO

**ENSO — El Niño-Southern Oscillation**
Fenómeno climático cíclico que alterna entre El Niño (aguas cálidas en el Pacífico → sequía en Colombia) y La Niña (aguas frías → lluvias intensas en Colombia).

**Fenómeno del Niño (en Colombia)**
Durante El Niño, la Zona de Convergencia Intertropical (ZCIT) se desplaza, reduciendo las lluvias sobre las cuencas andinas colombianas. Resultado: aportes bajos, embalses que no se recuperan, riesgo de racionamiento.

**ONI — Oceanic Niño Index**
Índice oficial de NOAA que mide la anomalía de temperatura superficial del mar en el Pacífico central. Valores >+0.5°C por 5 meses consecutivos = El Niño. El proyecto usa la SST directa de ERA5 en lugar del ONI mensual.

**MEI — Multivariate ENSO Index**
Versión más completa del ONI que incluye presión atmosférica, viento y temperatura del mar. Más sensible para detectar el inicio del fenómeno.

**ZCIT — Zona de Convergencia Intertropical**
Banda de baja presión cerca del ecuador donde convergen los vientos alisios de ambos hemisferios, generando lluvias intensas. Su desplazamiento durante El Niño determina el impacto sobre las cuencas colombianas.

---

## Unidades clave

| Símbolo | Nombre | Equivalencia útil |
|---|---|---|
| Mm³ | Millones de metros cúbicos | Volumen de agua |
| m³/s | Metros cúbicos por segundo | Caudal instantáneo |
| m³ | Metros cúbicos | Masa de agua (aportes en el dataset) |
| GWh | Gigavatio-hora | Energía eléctrica equivalente |
| kWh | Kilovatio-hora | 1 GWh = 1,000,000 kWh |
| hPa | Hectopascal | Presión atmosférica (1 hPa = 100 Pa) |
| m³/m³ | Metros cúbicos por metro cúbico | Humedad volumétrica del suelo |
| % cap. útil | Porcentaje de capacidad útil | El indicador de alerta del sistema |
