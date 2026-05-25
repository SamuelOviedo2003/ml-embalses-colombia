# Reproducibility Checklist — Proyecto Embalses Colombia

**Curso:** Aprendizaje de Máquina Aplicado  
**Estudiantes:** Isis Catitza Amaya Arbelaez, Santiago Alberto Rozo Silva, Samuel Oviedo Paz  
**Repositorio:** [ml-embalses-colombia](https://github.com/SamuelOviedo2003/ml-embalses-colombia.git)

---

## Entorno

- [x] Versión mínima de Python verificada en el notebook (`Python >= 3.7`)
- [x] Versión mínima de scikit-learn verificada (`>= 1.0.1`)
- [x] Librerías instaladas explícitamente en el notebook (`numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy`, `scikit-learn`, `category_encoders`, `xgboost`, `catboost`, `lightgbm`)

---

## Datos

- [x] Ruta del dataset definida en una variable central (`data_path = Path("../Datasets/dataset_final.csv")`)
- [x] Target definido en una variable central (`TARGET = "reserva_pct"`)
- [x] Embalses excluidos documentados explícitamente en el código (`AGREGADO_SIN`, `ITUANGO`, `SOGAMOSO`, `ELQUIMBO`)
- [x] Conversión de fechas documentada y reproducible (`pd.to_datetime`)

---

## Semillas y aleatoriedad

- [x] Semilla global definida en una sola variable (`SEED = 72`)
- [x] `SEED` aplicado en todos los modelos: DecisionTree, XGBoost, Random Forest, Extra Trees, LightGBM

---

## División de datos

- [x] Split temporal respetando el orden cronológico (sin shuffle aleatorio)
- [x] Tamaños del split verificados y reportados: **88,830 train / 3,213 test**
- [x] Estabilidad estadística del target verificada entre train y test (medias cercanas: 62.52 vs 57.05)
- [x] Validación cruzada temporal con `TimeSeriesSplit(n_splits=5)`

---

## Preprocesamiento y Feature Engineering

- [x] Todo el preprocesamiento encapsulado en `sklearn Pipeline` (sin transformaciones sueltas fuera del pipeline)
- [x] Features de lag, rolling mean, desviación estándar móvil y acumulados calculados con `shift(1)` para evitar leakage
- [x] Estrategia de imputación documentada por tipo de modelo (e.g., `median` para LightGBM/RF, distinto para otros)
- [x] Escalado numérico aplicado selectivamente (desactivado para modelos basados en árboles)

---

## Modelos

- [x] Hiperparámetros de todos los modelos definidos explícitamente en el código
- [x] Misma función de evaluación (`evaluate_pipeline`) usada para todos los modelos
- [x] Baseline naive definido y evaluado con la misma metodología

---

## Métricas y Resultados

- [x] Métricas reportadas: RMSE, MAE, R², MASE
- [x] Baseline naive incluido en la comparación final
- [x] Resultados de validación cruzada y evaluación en test reportados por separado
- [x] Importancia de variables calculada y visualizada para todos los modelos
- [x] Análisis de residuales por embalse incluido
