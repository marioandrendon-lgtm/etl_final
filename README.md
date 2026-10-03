# ETL MIO

Proyecto académico de ETL para integrar, validar, auditar y cargar información operacional del SITM-MIO en PostgreSQL / Supabase.

La implementación utiliza Python y una estructura orientada a capas de extracción, calidad, carga y consulta.

## 1. Alcance actual

El proyecto soporta actualmente los siguientes conjuntos de datos:

- Usos
- UsosValidador
- Día Tipo
- Plan de Servicios de Operación (PSO)
- Coordenadas de paradas (archivo Excel multihoja)

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
├── src/
│   ├── database/
│   │   └── database.py
│   │
│   ├── extract/
│   │   ├── readers.py
│   │   ├── pso_reader.py
│   │   └── coordenadas_reader.py
│   │
│   ├── load/
│   │   ├── loaders.py
│   │   ├── pso_loader.py
│   │   └── coordenadas_loader.py
│   │
│   ├── quality/
│   │   └── audit.py
│   │
│   ├── transform/
│   │
│   └── utils/
│       └── utils.py
│
├── reportes/
│   ├── Avance2.py
│   └── salidas/
│       ├── silver/
│       ├── gold/
│       ├── kpi/
│       └── graficos/
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

`sql/01_setup.sql` fue retirado y ya no es un paso de inicialización. Para coordenadas y las vistas de consulta, los scripts documentados son `sql/03_coordenadas.sql` y `sql/04_silver_gold.sql` cuando estén presentes en el repositorio. Antes de ejecutar cargas, verifique que las tablas de auditoría y Bronze requeridas existan en la base de datos; este README no sustituye sus migraciones.

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

# 9. Coordenadas de paradas

El subcomando `coordenadas` lee `COORDENADAS_PARADAS.xlsx` y envía la carga al módulo `src/load/coordenadas_loader.py`:

```powershell
python main.py coordenadas --file "E:\ruta\COORDENADAS_PARADAS.xlsx"
```

La integración de las versiones o snapshots PSO se consulta posteriormente desde `silver.dim_parada_actual`, `silver.puente_ruta_parada` y `gold.kpi_coordenadas`, si dichas vistas existen. Registre la fecha de vigencia de cada snapshot y compruebe los códigos y las coordenadas antes de usar sus resultados.

---

# 10. Auditoría

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

# 11. Idempotencia

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

# 12. Vigencias PSO

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

# 13. Transacciones

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

# 14. Manejo de valores nulos

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

# 15. API

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

# 16. Reportes Silver, Gold y calidad

El subcomando `reportes` invoca `reportes/Avance2.py` y consulta PostgreSQL para producir extractos CSV e imágenes PNG:

```powershell
python main.py reportes
```

| Capa | Objetos consultados | Salidas |
| --- | --- | --- |
| Auditoría | `carga.archivo_etl`, `carga.dataset_etl` | `reportes/salidas/kpi/auditoria_cargas.csv`, consistencia y duplicados |
| Silver | `silver.fact_usos_hora`, `silver.dim_parada_actual`, `silver.puente_ruta_parada` | `reportes/salidas/silver/*.csv` |
| Gold | `gold.demanda_diaria`, `gold.demanda_estacion_dia_tipo` | `reportes/salidas/gold/*.csv` |
| KPIs | `gold.kpi_carga_dataset`, `gold.kpi_carga_archivo`, `gold.kpi_coordenadas` | `reportes/salidas/kpi/*.csv` |
| Gráficos | Consultas de demanda y calidad | `reportes/salidas/graficos/*.png` |

La conexión de reportes requiere `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD` en el entorno. El módulo adjunto utiliza `SQLAlchemy` y `psycopg` para PostgreSQL, y `pandas` y `matplotlib` para la generación de salidas. Si se habilita exportación a Excel, se necesita `openpyxl` y una conversión de las fechas con zona horaria en una copia del DataFrame antes de exportar.

**Estado de la copia disponible:** `reportes/Avance2.py` define `get_engine()` pero llama a `get_connection()` sin definirla; debe integrarse la corrección de conexión antes de ejecutar `reportes`. La función `export_if_data` de esa copia acepta solo dos argumentos y exporta CSV. La generación de XLSX y las etiquetas de datos en gráficos discutidas hoy no aparecen todavía en los archivos adjuntos, por lo cual no se presentan como funcionalidades verificadas.

Los reportes actuales tratan auditoría de cargas y demanda operacional. No implementan todavía la conciliación financiera completa entre tap, autorización, ledger, clearing y banco.

---

# 17. Comandos disponibles

Consultar ayuda general:

```powershell
python main.py --help
```

Los subcomandos principales son:

```text
usos
dia-tipo
pso
coordenadas
reportes
```

Consultar la ayuda específica de PSO:

```powershell
python main.py pso --help
```

---

# 18. Flujo de desarrollo Git

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

# 19. Estado actual

El proyecto cuenta con una línea base funcional para:

- conexión directa a PostgreSQL;
- carga de Usos;
- carga de UsosValidador;
- carga de Día Tipo;
- carga de PSO;
- comando de carga de coordenadas;
- comando de generación de reportes Silver/Gold, KPI y gráficos;
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

La ejecución de los reportes requiere resolver la discrepancia de conexión señalada en la sección 16 y disponer de las vistas SQL correspondientes. La sincronización Git y el estado real del repositorio no se verificaron con los archivos adjuntos.
