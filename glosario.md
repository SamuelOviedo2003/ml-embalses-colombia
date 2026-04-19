# Glosario del proyecto — Embalses y sistema eléctrico colombiano

---

## Sistema eléctrico

**SIN — Sistema Interconectado Nacional**
Red eléctrica que conecta la generación y el consumo de energía en la mayor parte del territorio colombiano. Está operado y supervisado por XM. La mayoría de embalses del país hacen parte del SIN.

**XM**
Empresa filial de ISA encargada de operar el SIN y administrar el mercado de energía mayorista en Colombia. Es la principal fuente de datos históricos de reservas, aportes, vertimientos y generación.

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

## Las tres variables del dataset

**Reservas energéticas (objetivo del proyecto — TARGET)**
Agua almacenada en la zona útil de los embalses, expresada en energía equivalente (GWh) o en porcentaje de la capacidad útil total del SIN. El seguimiento diario en % es la métrica oficial que usa XM para alertas.
- `Volumen Útil Diario %` → cuánto le queda al sistema respecto a su máximo posible.
- Umbral crítico histórico: aproximadamente **30%** activa alertas oficiales.

**Aportes**
Agua que llega a los embalses y plantas desde los ríos (lluvia + escorrentía de cuencas). Se expresan en m³/s y también en GWh/día equivalente (dependiendo de la eficiencia de las turbinas). El `Aportes %` compara el caudal actual con la media histórica del mismo mes — si es <100% hay déficit hídrico.
- Durante El Niño: aportes caen consistentemente por debajo de la media histórica.

**Vertimientos**
Agua que se evacua del embalse cuando supera su nivel máximo físico, generalmente en temporadas de lluvia. Es agua que se "pierde" sin generar electricidad. Durante El Niño los vertimientos son prácticamente cero (el embalse nunca se llena de más).

---

## Hidrología y clima

**Cuenca hidrográfica**
Área geográfica cuyas aguas superficiales drenan hacia un mismo río o embalse. Los aportes al embalse dependen de la lluvia que cae en su cuenca.

**Región hidrológica**
Agrupación geográfica de cuencas con comportamiento hidrológico similar. XM divide Colombia en varias regiones (Caribe, Andina, Pacífico, Orinoquía, Amazonía).

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
Índice oficial de NOAA que mide la anomalía de temperatura superficial del mar en el Pacífico central. Valores > +0.5°C por 5 meses consecutivos = El Niño. Es el predictor climático clave para este proyecto.

**MEI — Multivariate ENSO Index**
Versión más completa del ONI que incluye presión atmosférica, viento y temperatura del mar. Más sensible para detectar el inicio del fenómeno.

---

## Unidades clave

| Símbolo | Nombre | Equivalencia útil |
|---|---|---|
| Mm³ | Millones de metros cúbicos | Volumen de agua |
| m³/s | Metros cúbicos por segundo | Caudal instantáneo |
| GWh | Gigavatio-hora | Energía eléctrica equivalente |
| kWh | Kilovatio-hora | 1 GWh = 1,000,000 kWh |
| % cap. útil | Porcentaje de capacidad útil | El indicador de alerta del sistema |
