# ETL MIO V2

## Regla de carga

### Archivo Usos(fecha)

Un solo archivo físico contiene:

- hoja `Usos`
- hoja `UsosValidador`

El archivo se registra una vez en:

`carga.archivo_etl`

y genera dos registros en:

`carga.dataset_etl`

- `USOS`
- `USOS_VALIDADOR`

### Día Tipo

El archivo Día Tipo se carga mediante un procedimiento independiente y genera:

- un archivo `DIA_TIPO`
- un dataset `DIA_TIPO`

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copiar `.env.example` a `.env` y configurar `DATABASE_URL`.

## Inicializar base

Ejecutar:

`sql/01_setup_v2.sql`

## Cargar archivo Usos

```bash
python main.py usos --file "E:\mrendon\Documents\2026\Maestria\ETL\Proyecto\data\bronze\recaudo\usos\260202 USOS.xlsx"
```

## Cargar carpeta 

```bash
python main.py usos --folder "E:\mrendon\Documents\2026\Maestria\ETL\Proyecto\data\bronze\recaudo\usos"
```

###Cargar carpeta recursiva
```bash 
python main.py usos --folder "E:\...\recaudo\usos" --recursive
```

## Cargar Día Tipo

```bash
python -m src.main dia-tipo --file "D:/Datos/Demanda2026.xlsx" --sheet "Hoja2"
```

## API

```bash
uvicorn api.main:app --reload
```

Endpoints:

- `POST /api/v1/cargas/usos`
- `POST /api/v1/cargas/dia-tipo`
- `GET /api/v1/consultas/usos-validador-diarios`
- `GET /api/v1/consultas/auditoria`
- `GET /health`

## Idempotencia

Nivel físico:

`carga.archivo_etl.sha256_archivo`

Nivel lógico:

`carga.dataset_etl(tipo_dataset, sha256_contenido)`

Nivel de fila:

`unique(dataset_id, fila_origen)`

## Transacción

La carga de un archivo Usos se ejecuta en una sola transacción PostgreSQL:

archivo -> USOS -> USOS_VALIDADOR -> COMMIT

Si se presenta una excepción durante la transacción se ejecuta ROLLBACK.
