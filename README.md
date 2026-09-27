# ETL MIO

Proyecto académico de ETL para integrar, validar, auditar y cargar información operacional del SITM-MIO en PostgreSQL / Supabase.

La implementación utiliza Python y una estructura orientada a capas de extracción, calidad, carga y consulta.

## 1. Alcance actual

El proyecto soporta actualmente los siguientes conjuntos de datos:

- Usos
- UsosValidador
- Día Tipo
- Plan de Servicios de Operación (PSO)

La carga se realiza directamente sobre PostgreSQL mediante `psycopg`, manteniendo mecanismos de:

- auditoría de archivos;
- auditoría de datasets;
- control de duplicados;
- hashes SHA-256;
- trazabilidad por archivo;
- trazabilidad por hoja para PSO;
- transacciones PostgreSQL;
- rollback ante errores;
- carga individual o por carpeta.

---

## 2. Arquitectura general

La estructura principal del proyecto es:

```text
ETL-MIO/
│
├── api/
│   ├── main.py
│   └── routes/
│
├── config/
│   ├── config.py
│   └── config.yaml
│
├── sql/
│   └── 01_setup.sql
│
├── src/
│   ├── database/
│   │   └── database.py
│   │
│   ├── extract/
│   │   ├── readers.py
│   │   └── pso_reader.py
│   │
│   ├── load/
│   │   ├── loaders.py
│   │   └── pso_loader.py
│   │
│   ├── quality/
│   │   └── audit.py
│   │
│   ├── transform/
│   │
│   └── utils/
│       └── utils.py
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

La carpeta `test/` se mantiene fuera de la sincronización del repositorio.

---

## 3. Configuración

La configuración del proyecto se administra mediante:

```text
config/config.yaml
```

y la lógica de lectura correspondiente se encuentra en:

```text
config/config.py
```

No deben almacenarse en el repositorio contraseñas, tokens, claves privadas ni credenciales reales de conexión.

---

## 4. Instalación

Crear el entorno virtual:

```powershell
python -m venv .venv
```

Activarlo en Windows:

```powershell
.venv\Scripts\activate
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

---

## 5. Inicialización de la base de datos

Ejecutar el script:

```text
sql/01_setup.sql
```

Este script contiene la estructura base utilizada por el ETL para los esquemas de carga, almacenamiento Bronze y consulta.

---

# 6. Carga de Usos

Un archivo físico de recaudo contiene principalmente las hojas:

```text
Usos
UsosValidador
```

El archivo físico se registra una vez en:

```text
carga.archivo_etl
```

y genera datasets independientes en:

```text
carga.dataset_etl
```

para:

```text
USOS
USOS_VALIDADOR
```

## Cargar un archivo

```powershell
python main.py usos --file "E:\ruta\260202 USOS.xlsx"
```

## Cargar una carpeta

```powershell
python main.py usos --folder "E:\ruta\recaudo\usos"
```

## Cargar una carpeta de forma recursiva

```powershell
python main.py usos --folder "E:\ruta\recaudo\usos" --recursive
```

---

# 7. Carga de Día Tipo

La información de Día Tipo se procesa mediante un procedimiento independiente.

Genera:

```text
tipo_archivo  = DIA_TIPO
tipo_dataset  = DIA_TIPO
```

Ejemplo:

```powershell
python main.py dia-tipo --file "E:\ruta\Demanda2026.xlsx" --sheet "Hoja2"
```

---

# 8. Carga del Plan de Servicios de Operación — PSO

El ETL incorpora carga específica para archivos del Plan de Servicios de Operación.

El archivo debe contener en su nombre una fecha de inicio de vigencia con el patrón:

```text
PSO_YYMMDD
```

Ejemplo:

```text
Reporte Definitivo_PSO_260330_SS_Rev.xlsx
```

corresponde a:

```text
2026-03-30
```

## Hojas DET

El proceso identifica automáticamente las hojas cuyo nombre inicia por:

```text
DET
```

Un PSO válido puede contener actualmente:

```text
3 o 4 hojas DET
```

Ejemplos:

```text
DET-DHABIL
DET-SAB
DET-DOM
DET-DOMFEST
```

La denominación específica puede variar entre archivos.

Cada hoja es:

1. detectada;
2. validada;
3. normalizada;
4. auditada individualmente;
5. cargada en PostgreSQL;
6. integrada al dataset general del PSO.

## Encabezados

El lector del PSO identifica la fila real de encabezados de cada hoja DET.

Esto permite procesar archivos en los que los encabezados no comienzan necesariamente en la primera fila.

Las columnas requeridas para el modelo se conservan y las columnas adicionales no utilizadas por la versión actual del modelo pueden ser ignoradas durante la selección de campos.

## Horarios operacionales

Los campos:

```text
desde
hasta
duracion
```

se manejan como intervalos temporales.

Esto permite conservar correctamente horarios operacionales superiores a las 24 horas, por ejemplo:

```text
23:50
24:06
25:15
```

sin transformarlos incorrectamente a horas del día siguiente.

## Cargar un archivo PSO

```powershell
python main.py pso --file "E:\ruta\Reporte Definitivo_PSO_260330_SS_Rev.xlsx"
```

## Cargar una carpeta de PSO

```powershell
python main.py pso --folder "E:\ruta\pso"
```

## Carga recursiva

```powershell
python main.py pso --folder "E:\ruta\pso" --recursive
```

---

# 9. Auditoría

La auditoría se gestiona principalmente mediante:

```text
carga.archivo_etl
carga.dataset_etl
```

Para PSO se incorpora además auditoría a nivel de hoja.

Esto permite mantener trazabilidad sobre:

```text
archivo físico
    ↓
dataset
    ↓
hojas DET
    ↓
registros Bronze
```

Entre los datos registrados se incluyen:

- nombre del archivo;
- hash físico;
- hash lógico;
- tipo de archivo;
- tipo de dataset;
- cantidad de filas leídas;
- cantidad de filas cargadas;
- cantidad de filas rechazadas;
- estado de la carga;
- fechas del proceso;
- mensajes de error;
- hoja de origen;
- fila de origen.

---

# 10. Idempotencia

El ETL implementa controles para evitar cargas duplicadas.

## Nivel físico

Se utiliza:

```text
carga.archivo_etl.sha256_archivo
```

Si exactamente el mismo archivo ya fue procesado, la carga retorna:

```text
DUPLICADO
```

con motivo:

```text
sha256_archivo
```

## Nivel lógico

Los datasets utilizan un hash SHA-256 construido sobre su contenido normalizado.

Esto permite identificar contenido repetido incluso cuando el archivo físico sea distinto.

## PSO

Para PSO se calculan:

```text
SHA-256 del archivo físico
SHA-256 de cada hoja DET
SHA-256 lógico del dataset completo
```

---

# 11. Vigencias PSO

Cada PSO tiene una fecha de inicio de vigencia obtenida desde el nombre del archivo.

Conceptualmente:

```text
PSO A
fecha_inicio = 2026-03-30

PSO B
fecha_inicio = 2026-04-15
```

La vigencia del PSO A termina el día anterior al inicio del PSO B:

```text
2026-04-14
```

El último PSO vigente puede utilizar como fecha final:

```text
9999-12-31
```

La actualización de vigencias se realiza después de completar satisfactoriamente una carga PSO.

---

# 12. Transacciones

La carga se ejecuta utilizando transacciones PostgreSQL.

Para un archivo de Usos:

```text
archivo
   ↓
USOS
   ↓
USOS_VALIDADOR
   ↓
COMMIT
```

Para un PSO:

```text
archivo
   ↓
dataset PSO
   ↓
hoja DET 1
   ↓
hoja DET 2
   ↓
hoja DET 3
   ↓
hoja DET 4, cuando existe
   ↓
actualización de auditoría
   ↓
recalculo de vigencias
   ↓
COMMIT
```

Si ocurre una excepción dentro de la transacción:

```text
ROLLBACK
```

evitando dejar una carga parcialmente confirmada.

---

# 13. Manejo de valores nulos

Durante la transformación, Pandas puede representar valores faltantes mediante:

```text
pd.NA
NaN
NaT
```

Antes de enviarlos a PostgreSQL, la capa de carga los normaliza a:

```text
None
```

para que sean almacenados correctamente como:

```sql
NULL
```

---

# 14. API

La API se ejecuta mediante FastAPI.

```powershell
uvicorn api.main:app --reload
```

Actualmente la estructura del repositorio contiene rutas para carga y consulta.

Entre los endpoints implementados en la línea base se encuentran:

```text
POST /api/v1/cargas/usos
POST /api/v1/cargas/dia-tipo
GET  /api/v1/consultas/usos-validador-diarios
GET  /api/v1/consultas/auditoria
GET  /health
```

La carga PSO se encuentra actualmente implementada en el proceso ETL por línea de comandos.

---

# 15. Comandos disponibles

Consultar ayuda general:

```powershell
python main.py --help
```

Los subcomandos principales son:

```text
usos
dia-tipo
pso
```

Consultar la ayuda específica de PSO:

```powershell
python main.py pso --help
```

---

# 16. Flujo de desarrollo Git

El desarrollo debe realizarse mediante ramas de trabajo.

Para el desarrollo PSO:

```text
feature/pso-etl
```

Flujo recomendado:

```text
main
  ↓
feature/pso-etl
  ↓
desarrollo
  ↓
validación
  ↓
commit
  ↓
rebase con origin/main
  ↓
push
  ↓
revisión
  ↓
merge
```

Los archivos de pruebas locales y configuraciones sensibles deben permanecer fuera del seguimiento cuando corresponda.

---

# 17. Estado actual

El proyecto cuenta con una línea base funcional para:

- conexión directa a PostgreSQL;
- carga de Usos;
- carga de UsosValidador;
- carga de Día Tipo;
- carga de PSO;
- auditoría de archivos;
- auditoría de datasets;
- auditoría por hojas PSO;
- hashes físicos y lógicos;
- control de duplicados;
- procesamiento por archivo;
- procesamiento por carpeta;
- procesamiento recursivo;
- transacciones;
- vigencias PSO;
- API básica de carga y consulta.

El desarrollo continúa orientado a consolidar la arquitectura ETL y ampliar posteriormente las capas Silver y Gold.