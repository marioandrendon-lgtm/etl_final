# ETL MIO

Proyecto académico de ETL para integrar, validar, auditar, consultar y generar productos analíticos a partir de información operacional del SITM-MIO, utilizando Python y PostgreSQL/Supabase.

La versión actual combina dos formas de ejecución:

1. **CLI (`main.py`)** para cargas por archivo/carpeta y generación de reportes.
2. **FastAPI (`api/main.py`)** para cargas controladas y consultas vía HTTP/Swagger.

> **Estado de esta versión:** incluye Usos/UsosValidador, Día Tipo, Plan de Servicios de Operación (PSO), Coordenadas de Paradas, auditoría, vistas Silver/Gold, KPIs, reportes y FastAPI. El componente GTFS versionado está diseñado en el proyecto, pero **todavía no forma parte de los archivos de esta versión del repositorio**; por tanto, no se documenta como funcionalidad ejecutable.

---

## 1. Objetivo

Construir una línea base de integración de datos que permita:

- cargar fuentes operacionales heterogéneas;
- mantener trazabilidad de cada archivo y dataset procesado;
- detectar cargas duplicadas mediante hashes SHA-256;
- controlar estados de carga y errores;
- conservar vigencias de PSO y snapshots de coordenadas;
- exponer consultas operacionales mediante FastAPI;
- construir vistas Silver y Gold para análisis;
- generar KPIs, archivos de salida y gráficos reproducibles.

---

## 2. Arquitectura tecnológica

```text
                         ┌─────────────────────────────┐
                         │      Archivos fuente        │
                         │ Excel / datos operacionales │
                         └──────────────┬──────────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │       Extract / Readers     │
                         │ src/extract/*.py            │
                         └──────────────┬──────────────┘
                                        │
                    ┌───────────────────▼───────────────────┐
                    │       Validación / Auditoría          │
                    │ hash archivo + hash contenido         │
                    │ carga.archivo_etl / dataset_etl       │
                    └───────────────────┬───────────────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │          BRONZE             │
                         │ datos detallados/auditables │
                         └──────────────┬──────────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │          SILVER             │
                         │ datos normalizados/vigentes │
                         └──────────────┬──────────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │           GOLD              │
                         │ KPIs / agregados / análisis │
                         └──────────┬───────────┬──────┘
                                    │           │
                       ┌────────────▼───┐   ┌──▼─────────────┐
                       │   FastAPI      │   │ reportes/      │
                       │ consultas HTTP │   │ Avance2.py     │
                       └────────────────┘   └────────────────┘
```

### Capas

| Capa      | Propósito                               | Implementación actual                      |
|---        |---                                      |---                                         |
| Fuente    | Archivos recibidos                      | Excel / archivos locales                   |
| Extract   | Lectura, normalización inicial          | `src/extract/`                             |
| Auditoría | Trazabilidad, hash, estados, duplicados | `src/quality/audit.py` + esquema `carga`   |
| Bronze    | Persistencia detallada de origen        | esquema `bronze`                           |
| Silver    | Datos integrados y normalizados         | vistas del esquema `silver`                |
| Gold      | KPIs y agregaciones                     | vistas del esquema `gold`                  |
| Consulta  | Exposición de vistas operacionales      | esquema `consulta` + FastAPI               |
| Reportes  | Extracts CSV, KPIs y gráficos           | `reportes/Avance2.py`                      | 

---

## 3. Estructura del repositorio

```text
Proyecto/
│
├── api/
│   ├── __init__.py
│   ├── main.py
│   └── routes/
│       ├── __init__.py
│       ├── cargas.py
│       └── consultas.py
│
├── config/
│   ├── __init__.py
│   ├── config.py
│   └── config.yaml
│
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── notebooks/
│   ├──__init__.py
│   └── Avance2.ipynb
│
├── reportes/
│   ├── __init__.py
│   ├── Avance2.py
│   └── salidas/               # generado localmente; no se versiona
│
├── src/
│   ├── database/
│   │   └── database.py
│   ├── extract/
│   │   ├── readers.py
│   │   ├── pso_reader.py
│   │   └── coordenadas_reader.py
│   ├── load/
│   │   ├── loaders.py
│   │   ├── pso_loader.py
│   │   └── coordenadas_loader.py
│   ├── quality/
│   │   └── audit.py
│   ├── transform/
│
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

---

## 4. Requisitos

### Software recomendado

- Windows 11 o Linux/macOS equivalente.
- Python **3.12** recomendado para reproducir el entorno validado.
- PostgreSQL accesible directamente o mediante Supabase.
- Git.
- Visual Studio Code recomendado.

Durante la validación del proyecto se comprobó funcionamiento con:

```text
Python       3.12.10
FastAPI      0.142.2
Uvicorn      0.54.0
SQLAlchemy   2.1.3
```

No es obligatorio fijar exactamente estas versiones si `requirements.txt` instala versiones compatibles.

### Dependencia SQLAlchemy

El requerimiento debe corresponder a la rama existente 2.x. Se recomienda:

```text
SQLAlchemy>=2.0.36,<3.0
```
---

## 5. Crear el entorno virtual

Desde la raíz del proyecto:

```powershell
py -3.12 -m venv .venv
```

Activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Actualizar herramientas base:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

Validar:

```powershell
python --version
python -m pip --version
```

> `.venv/` no debe incorporarse al repositorio Git. Si no está ya presente en `.gitignore`, agregar `.venv/`.

---

## 6. Configuración de variables de entorno

Copiar `.env.example` como `.env`:

```powershell
Copy-Item .env.example .env
```

Completar las variables:

```dotenv
# SUPABASE
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=etl-raw

# ETL
ETL_BATCH_SIZE=1000

# POSTGRESQL
DB_HOST=
DB_PORT=5432
DB_NAME=postgres
DB_USER=
DB_PASSWORD=

# POOL
DB_POOL_MIN=0
DB_POOL_MAX=5
```

### Importante

`config/config.py` valida actualmente la existencia de:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DB_HOST`
- `DB_USER`
- `DB_PASSWORD`

Por tanto, deben estar definidas aunque una ejecución concreta utilice principalmente la conexión PostgreSQL.

Nunca subir `.env`, contraseñas, claves o tokens al repositorio.

---

## 7. Conexión a PostgreSQL / Supabase

La conexión se administra en:

```text
src/database/database.py
```

El módulo implementa un `ConnectionPool` de `psycopg_pool` y expone:

```python
create_pool()
get_pool()
get_connection()
close_pool()
```

El patrón correcto para cualquier consulta es:

```python
from src.database.database import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("select 1")
        resultado = cur.fetchone()
```

El módulo mantiene internamente `_pool` y entrega las conexiones mediante `get_connection()`.

La conexión utiliza actualmente:

```text
sslmode=require
connect_timeout=10
```

---

## 8. Inicialización de base de datos

```text
Se debe validar con los autores el acceso a la creación de la base de datos
```


## 9. Modelo de auditoría e idempotencia

La lógica de auditoría se concentra en:

```text
src/quality/audit.py
```

Principales entidades:

### `carga.archivo_etl`

Representa el archivo físico recibido.

Conceptualmente registra:

```text
archivo_id
nombre_archivo
ruta/origen
sha256_archivo
tipo_archivo
estado
filas
vigencia (cuando aplica)
timestamps
error
```

### `carga.dataset_etl`

Representa un dataset lógico extraído de un archivo.

Un mismo archivo de recaudo puede producir, por ejemplo:

```text
USOS
USOS_VALIDADOR
```

### `carga.hoja_etl`

Usada por PSO para mantener auditoría individual por hoja `DET`.

### Reglas de deduplicación

El diseño utiliza dos niveles:

1. **Hash SHA-256 del archivo físico** para detectar archivos idénticos.
2. **Hash del contenido normalizado** para detectar datasets lógicamente duplicados aunque el archivo físico cambie.

No se deben eliminar duplicados silenciosamente: la ejecución debe quedar registrada con su estado correspondiente.

---

# 10. Ejecución por línea de comandos

Mostrar ayuda general:

```powershell
python main.py --help
```

---

## 10.1 Carga de Usos / UsosValidador

El archivo Excel contiene principalmente las hojas:

```text
Usos
UsosValidador
```

### Un archivo

```powershell
python main.py usos --file "D:\ruta\260202 USOS.xlsx"
```

### Una carpeta

> En `main.py`, el argumento se denomina `--carpeta`.

```powershell
python main.py usos --carpeta "D:\ruta\recaudo\usos"
```

### Carpeta recursiva

```powershell
python main.py usos --carpeta "D:\ruta\recaudo\usos" --recursive
```

### Destinos Bronze

```text
bronze.usos
bronze.usos_validador
```

La carga usa `COPY ... FROM STDIN` vía `psycopg` para inserción eficiente.

---

## 10.2 Carga de Día Tipo

```powershell
python main.py dia-tipo --file "D:\ruta\Demanda2026.xlsx" --sheet "Hoja2"
```

Destino:

```text
bronze.dia_tipo
```

El dataset se registra como:

```text
tipo_archivo = DIA_TIPO
tipo_dataset = DIA_TIPO
```

---

## 10.3 Carga del Plan de Servicios de Operación — PSO

### Archivo individual

```powershell
python main.py pso --file "D:\ruta\Reporte Definitivo_PSO_260330_SS_Rev.xlsx"
```

### Carpeta

```powershell
python main.py pso --folder "D:\ruta\pso"
```

### Carpeta recursiva

```powershell
python main.py pso --folder "D:\ruta\pso" --recursive
```

### Fecha de vigencia

El lector extrae la fecha inicial desde el nombre del archivo usando el patrón:

```text
PSO_YYMMDD
```

Ejemplo:

```text
Reporte Definitivo_PSO_260330_SS_Rev.xlsx
                        └─ 2026-03-30
```

### Hojas DET

El proceso detecta las hojas cuyo nombre comienza por:

```text
DET
```

Ejemplos observados:

```text
DET-DHABIL
DET-SAB
DET-DOM
DET-DOMFEST
```

Cada hoja se:

1. detecta;
2. lee con identificación dinámica de encabezados;
3. normaliza;
4. calcula hash de contenido;
5. registra en `carga.hoja_etl`;
6. carga en `bronze.pso_detalle`;
7. integra al dataset PSO auditado.

### Llave de idempotencia en detalle

`bronze.pso_detalle` usa la restricción:

```text
(hoja_id, fila_origen)
```

La vigencia se mantiene mediante:

```text
fecha_inicio_vigencia
fecha_fin_vigencia
```

El script `02_setup_pso.sql` incorpora además la función:

```text
carga.recalcular_vigencias_pso()
```

---

## 10.4 Carga de Coordenadas de Paradas

```powershell
python main.py coordenadas --file "D:\ruta\COORDENADAS_PARADAS.xlsx"
```

El lector procesa un archivo Excel multihoja y conserva el snapshot asociado a su vigencia.

Destino:

```text
bronze.coordenadas_paradas
```

Campos principales:

```text
codigo_parada
tipo
nombre
rutas
latitud
longitud
fecha_inicio_vigencia
nombre_hoja
fila_origen
dataset_id
```

Controles de base de datos:

```text
latitud  entre -90 y 90
longitud entre -180 y 180
```

Llave lógica de ingestión:

```text
(dataset_id, nombre_hoja, fila_origen)
```

---

## 10.5 Generación de reportes

Crear/actualizar previamente las vistas Silver/Gold:

```text
sql/05_silver_gold.sql
```

Luego ejecutar:

```powershell
python main.py reportes
```

También puede ejecutarse directamente:

```powershell
python reportes/Avance2.py
```

Las salidas se generan bajo:

```text
reportes/salidas/
├── silver/
├── gold/
├── kpi/
└── graficos/
```

Estas salidas son artefactos generados y no están versionadas en Git.

---

# 11. Capas Silver y Gold

`sql/05_silver_gold.sql` define actualmente:

## Silver

### `silver.dim_dia_tipo`

Expone el Día Tipo vigente.

### `silver.fact_usos_hora`

Integra usos por hora con Día Tipo.

Relación principal:

```text
USOS.fecha → DIM_DIA_TIPO.fecha
```

### `silver.dim_parada_actual`

Snapshot vigente de cada parada. Selecciona la última vigencia cargada por `codigo_parada`.

### `silver.parada_snapshot`

Histórico de snapshots de coordenadas.

### `silver.puente_ruta_parada`

Desagrega la cadena de rutas de cada parada para construir una relación:

```text
codigo_parada ↔ codigo_ruta
```

## Gold

### `gold.demanda_diaria`

Demanda agregada por fecha y Día Tipo.

### `gold.demanda_estacion_dia_tipo`

Demanda por estación/servicio y Día Tipo.

### `gold.kpi_carga_dataset`

Indicadores de ejecución por tipo de dataset.

### `gold.kpi_carga_archivo`

Indicadores de carga de archivos físicos.

### `gold.kpi_coordenadas`

Indicadores de calidad de coordenadas por vigencia.

### `gold.kpi_fuentes_disponibles`

Inventario de datasets cargados y cobertura temporal.

---

# 12. FastAPI

La API se encuentra en:

```text
api/main.py
```

Configuración actual:

```text
Título:  API ETL MIO
Versión: 2.0.0
```

## 12.1 Iniciar API

Desde la raíz del proyecto y con `.venv` activo:

```powershell
python -m uvicorn api.main:app --reload
```

Salida esperada:

```text
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Application startup complete.
```

## 12.2 Swagger

Abrir:

```text
http://127.0.0.1:8000/docs
```

Documentación alternativa:

```text
http://127.0.0.1:8000/redoc
```

---

## 12.3 Health check

```http
GET /health
```

Respuesta esperada:

```json
{
  "status": "ok"
}
```

Prueba:

```powershell
curl.exe -i "http://127.0.0.1:8000/health"
```

---

## 12.4 Endpoints de carga

La API debe reutilizar los loaders existentes. La lógica ETL **no debe duplicarse dentro de FastAPI**.

### Usos

```http
POST /api/v1/cargas/usos
```

Loader:

```python
src.load.loaders.cargar_archivo_usos
```

Ejemplo:

```powershell
curl.exe -X POST `
  "http://127.0.0.1:8000/api/v1/cargas/usos" `
  -F "file=@D:\ruta\260202 USOS.xlsx"
```

### Día Tipo

```http
POST /api/v1/cargas/dia-tipo?sheet=Hoja2
```

Loader:

```python
src.load.loaders.cargar_dia_tipo
```

Ejemplo:

```powershell
curl.exe -X POST `
  "http://127.0.0.1:8000/api/v1/cargas/dia-tipo?sheet=Hoja2" `
  -F "file=@D:\ruta\Demanda2026.xlsx"
```

### PSO

```http
POST /api/v1/cargas/pso
```

Loader:

```python
src.load.pso_loader.cargar_archivo_pso
```

### Coordenadas

```http
POST /api/v1/cargas/coordenadas
```

Loader:

```python
src.load.coordenadas_loader.cargar_coordenadas
```

---

## 12.5 Endpoints de consulta

### Usos por validador/día

```http
GET /api/v1/consultas/usos-validador-diarios
```

Parámetros:

```text
fecha_inicio
fecha_fin
```

Las fechas deben enviarse en formato ISO 8601:

```text
YYYY-MM-DD
```

Correcto:

```text
2026-03-01
2026-03-05
```

Incorrecto:

```text
01/03/2026
05/03/2026
```

Ejemplo:

```powershell
curl.exe -i "http://127.0.0.1:8000/api/v1/consultas/usos-validador-diarios?fecha_inicio=2026-03-01&fecha_fin=2026-03-05"
```

La consulta usa la vista:

```text
consulta.resumen_usos_validador_dia
```

con los campos:

```text
fecha
dia_tipo
registros
total_usos_dia
```

### Auditoría

```http
GET /api/v1/consultas/auditoria?limite=100
```

Restricciones actuales:

```text
mínimo:   1
máximo:   1000
por defecto: 100
```

Fuente:

```text
consulta.auditoria_archivos
```

---

## 12.6 Patrón de conexión en FastAPI

Los endpoints de consulta deben importar:

```python
from src.database.database import get_connection
```

Y usar:

```python
with get_connection() as conn:
    with conn.cursor() as cur:
        ...
```

No usar:

```python
from src.database.database import pool
```

ni:

```python
with pool.connection() as conn:
```

porque `database.py` no expone una variable pública `pool`.

---

# 13. API: organización recomendada del código

```text
api/main.py
   │
   ├── /api/v1/cargas
   │      │
   │      └── api/routes/cargas.py
   │             │
   │             ├── src/load/loaders.py
   │             ├── src/load/pso_loader.py
   │             └── src/load/coordenadas_loader.py
   │
   └── /api/v1/consultas
          │
          └── api/routes/consultas.py
                 │
                 └── src/database/database.py
```

Principio de diseño:

```text
FastAPI = capa de exposición/orquestación
Loaders = lógica ETL
Database = conexión
Audit = trazabilidad
PostgreSQL = persistencia
```

---

# 14. Calidad de datos

La versión actual incorpora controles en diferentes niveles.

| Fuente          | Controles principales                                                                      |
|---              |---                                                                                         |
| Usos            | estructura de hojas, conversión de fechas, carga auditada, hash físico/lógico              |
| UsosValidador   | lectura/normalización, trazabilidad por dataset                                            |
| Día Tipo        | hoja configurable, fecha y Día Tipo, hash y auditoría                                      |
| PSO             | nombre/vigencia, hojas DET, encabezado dinámico, tipificación, auditoría por hoja, hashes  |
| Coordenadas     | múltiples hojas, vigencia, código de parada, latitud/longitud, hash y auditoría            |
| PostgreSQL      | constraints, llaves únicas, checks, FK y transacciones                                     |

### KPIs existentes

`gold.kpi_carga_dataset` calcula, entre otros:

```text
ejecuciones_dataset
datasets_cargados
datasets_duplicados
datasets_error
filas_leidas
filas_cargadas
filas_rechazadas
pct_carga
pct_rechazo
```

`gold.kpi_coordenadas` calcula:

```text
registros
paradas_unicas
registros_coordenadas_validas
pct_coordenadas_validas
```

---

# 15. Modelo de datos resumido

```text
carga.archivo_etl
      │ 1
      │
      ├─────────────── N carga.dataset_etl
      │                        │
      │                        ├── bronze.usos
      │                        ├── bronze.usos_validador
      │                        ├── bronze.dia_tipo
      │                        ├── bronze.pso_detalle
      │                        └── bronze.coordenadas_paradas
      │
      └─────────────── N carga.hoja_etl
                               │
                               └── bronze.pso_detalle

bronze.*
   │
   ▼
silver.*
   │
   ▼
gold.*
   │
   ├── FastAPI / consulta
   └── reportes/Avance2.py
```

### Llaves/relaciones relevantes

| Objeto                         | Llave o relación                                                |
|---                             |---                                                              |
| `carga.archivo_etl`            | `id` identifica archivo físico                                  |
| `carga.dataset_etl`            | `archivo_id → carga.archivo_etl.id`                             |
| `carga.hoja_etl`               | `archivo_id`, `dataset_id`; único `(archivo_id,nombre_hoja)`    |
| `bronze.pso_detalle`           | FK a archivo/dataset/hoja; único `(hoja_id,fila_origen)`        |
| `bronze.coordenadas_paradas`   | FK `dataset_id`; único `(dataset_id,nombre_hoja,fila_origen)`   |
| `silver.dim_parada_actual`     | selección vigente por `codigo_parada`                           |
| `silver.puente_ruta_parada`    | `codigo_parada ↔ codigo_ruta`                                   |

---

# 16. Notebook

El repositorio incluye:

```text
notebooks/Avance2.ipynb
```

Para abrirlo:

```powershell
python -m jupyter notebook
```

O utilizar directamente el soporte Jupyter de Visual Studio Code.

El notebook debe trabajar sobre la misma estructura de datos/configuración documentada para el proyecto y no debe incluir credenciales embebidas.

---

# 17. Git y archivos que no deben sincronizarse

Como mínimo, mantener fuera del repositorio:

```text
.venv/
.env
test/
__pycache__/
*.pyc
logs/
data/bronze/**
data/silver/**
data/gold/**
reportes/salidas/
.ipynb_checkpoints/
```

Después de modificar el proyecto:

```powershell
git status
git add .
git status
git commit -m "Actualiza ETL y FastAPI"
git pull --rebase
git push
```

Si `test/` ya estuvo versionado y se desea conservar localmente:

```powershell
git rm -r --cached test
```

Luego confirmar que `test/` esté incluido en `.gitignore`.

---

# 18. Pruebas rápidas después de clonar

## 18.1 Validar imports

```powershell
python -c "import pandas, psycopg, fastapi, uvicorn, sqlalchemy; print('Dependencias OK')"
```

## 18.2 Validar conexión

```powershell
python -c "from src.database.database import get_connection; c=get_connection(); print('DB OK'); c.close()"
```

## 18.3 Validar CLI

```powershell
python main.py --help
```

## 18.4 Validar API

```powershell
python -m uvicorn api.main:app --reload
```

Luego:

```powershell
curl.exe -i "http://127.0.0.1:8000/health"
```

## 18.5 Abrir Swagger

```text
http://127.0.0.1:8000/docs
```

---

# 19. Solución de problemas

## Error: `module 'click' has no attribute 'Choice'`

Síntoma de una instalación dañada de `click` en `.venv`.

Validar:

```powershell
python -c "import click; print(click.__file__); print(click.Choice)"
```

Si es necesario, reinstalar o recrear `.venv`.

---

## Error: `cannot import name 'Doc' from 'annotated_doc'`

Indica instalación incompleta/corrupta del entorno. La solución más segura si aparecen varios paquetes dañados es recrear `.venv` con Python 3.12 e instalar nuevamente `requirements.txt`.

---

## Error: `SQLAlchemy>=4.6.0`

La especificación es inválida. Utilizar una versión 2.x compatible:

```text
SQLAlchemy>=2.0.36,<3.0
```

---

## Error: `NameError: name 'pool' is not defined`

En `api/routes/consultas.py` utilizar:

```python
from src.database.database import get_connection
```

Y:

```python
with get_connection() as conn:
```

---

## Error de FastAPI con fechas `01/03/2026`

Los parámetros declarados como `date` deben enviarse en ISO:

```text
2026-03-01
```

No:

```text
01/03/2026
```

---

# 20. Flujo recomendado para un nuevo usuario

```text
1. Clonar repositorio
        ↓
2. Crear .venv con Python 3.12
        ↓
3. Instalar requirements.txt
        ↓
4. Crear .env desde .env.example
        ↓
5. Configurar PostgreSQL/Supabase
        ↓
6. Verificar que exista la línea base de BD
        ↓
7. Ejecutar SQL 02 → 04 → 05
        ↓
8. Ejecutar una carga CLI o FastAPI
        ↓
9. Revisar auditoría
        ↓
10. Generar Silver/Gold/reportes
        ↓
11. Consultar /docs y endpoints
```

---

# 21. GTFS — estado del diseño

El proyecto contempla como evolución la incorporación de GTFS como dataset en constante evolución, con las siguientes reglas arquitectónicas:

```text
GTFS_VERSION
   │
   ├── feed_version
   ├── hash del conjunto
   ├── vigencia
   └── histórico inmutable
```

Y una relación futura:

```text
PSO_VERSION 1 ───── 1 GTFS_VERSION
```

La regla prevista es que cada versión de PSO tenga asociada una versión GTFS. Para el alcance académico inicial, esa restricción no debe bloquear las cargas.

**Importante:** los módulos GTFS (`gtfs_reader`, `gtfs_loader`, `gtfs_quality`, pipeline y SQL correspondiente) todavía no están presentes en la versión del repositorio documentada por este README. No ejecutar endpoints GTFS hasta incorporarlos formalmente.

---

# 22. Consideraciones de seguridad

- No versionar `.env`.
- No registrar `SERVICE_ROLE_KEY`, contraseñas ni tokens en notebooks o logs.
- Usar conexiones TLS (`sslmode=require`).
- Mantener el acceso de base de datos con privilegios mínimos requeridos.
- No exponer FastAPI directamente a Internet con `--reload`.
- Para producción, incorporar autenticación/autorización, límites de tamaño de archivos, logging estructurado y manejo centralizado de excepciones.

---

# 23. Estado funcional resumido

| Componente                     | Estado                                           |
|---                             |---                                               |
| CLI Usos/UsosValidador         | Implementado                                     |
| CLI Día Tipo                   | Implementado                                     |
| CLI PSO                        | Implementado                                     |
| CLI Coordenadas                | Implementado                                     |
| Auditoría e idempotencia       | Implementado                                     |
| Silver / Gold                  | Implementado mediante SQL                        |
| Reportes y KPIs                | Implementado                                     |
| FastAPI /health                | Implementado y validado                          |
| FastAPI cargas Usos/Día Tipo   | Implementado                                     |
| FastAPI cargas PSO/Coordenadas | Incorporado en el ajuste actual                  |
| FastAPI consultas              | Implementado con `get_connection()`              |
| Swagger `/docs`                | Disponible                                       |
| GTFS versionado                | Diseñado, pendiente de incorporar al repositorio |
| DDL base completo desde cero   | Pendiente de consolidar en el repositorio        |

---

## Licencia / uso

Proyecto académico. Antes de utilizar información operacional real del SITM-MIO fuera del entorno autorizado, validar las políticas institucionales de seguridad, clasificación, tratamiento y publicación de datos aplicables.
