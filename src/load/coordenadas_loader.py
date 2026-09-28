from pathlib import Path

import pandas as pd

from src.database.database import get_connection
from src.extract.coordenadas_reader import read_coordinates_workbook
from src.quality.audit import (
    find_file_by_hash,
    create_file_record,
    find_content_duplicate,
    create_dataset_record,
    finish_dataset,
    finish_file,
)
from src.utils.utils import sha256_file, sha256_dataframe

HASH_COLUMNS = [
    "nombre_hoja",
    "fecha_inicio_vigencia",
    "codigo_parada",
    "tipo",
    "nombre",
    "rutas",
    "latitud",
    "longitud",
]


def _db_value(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _copy_coordinates(cur, dataset_id, df):
    sql = '''
    copy bronze.coordenadas_paradas (
        dataset_id,
        fila_origen,
        nombre_hoja,
        fecha_inicio_vigencia,
        codigo_parada,
        tipo,
        nombre,
        rutas,
        latitud,
        longitud
    )
    from stdin
    '''

    with cur.copy(sql) as copy:
        for row in df.itertuples(index=False):
            copy.write_row((
                dataset_id,
                _db_value(row.fila_origen),
                _db_value(row.nombre_hoja),
                _db_value(row.fecha_inicio_vigencia),
                _db_value(row.codigo_parada),
                _db_value(row.tipo),
                _db_value(row.nombre),
                _db_value(row.rutas),
                _db_value(row.latitud),
                _db_value(row.longitud),
            ))


def cargar_coordenadas(path: Path) -> dict:
    path = Path(path)
    file_hash = sha256_file(path)

    data = read_coordinates_workbook(path)
    df = data["dataframe_unificado"]

    content_hash = sha256_dataframe(df, HASH_COLUMNS)

    with get_connection() as conn:
        with conn.cursor() as cur:
            existing = find_file_by_hash(cur, file_hash)

        if existing:
            return {
                "estado": "DUPLICADO",
                "motivo": "sha256_archivo",
                "archivo_id": str(existing[0]),
                "archivo": path.name,
            }

        with conn.transaction():
            with conn.cursor() as cur:
                archivo_id = create_file_record(
                    cur=cur,
                    path=path,
                    file_type="COORDENADAS_PARADAS",
                    file_hash=file_hash,
                    source_date=data["fecha_max"],
                )

                duplicate_content = find_content_duplicate(
                    cur,
                    "COORDENADAS_PARADAS",
                    content_hash,
                )

                dataset_id = create_dataset_record(
                    cur=cur,
                    archivo_id=archivo_id,
                    dataset_type="COORDENADAS_PARADAS",
                    content_hash=content_hash,
                    rows_read=len(df),
                    fecha_min=data["fecha_min"],
                    fecha_max=data["fecha_max"],
                    status="DUPLICADO" if duplicate_content else "CARGANDO",
                )

                if duplicate_content:
                    finish_dataset(
                        cur,
                        dataset_id,
                        "DUPLICADO",
                        loaded=0,
                        rejected=0,
                        message="Contenido de coordenadas ya cargado previamente.",
                    )
                    finish_file(cur, archivo_id, "DUPLICADO")
                    return {
                        "estado": "DUPLICADO",
                        "motivo": "sha256_contenido",
                        "archivo_id": str(archivo_id),
                        "dataset_id": str(dataset_id),
                        "archivo": path.name,
                    }

                _copy_coordinates(cur, dataset_id, df)

                finish_dataset(
                    cur,
                    dataset_id,
                    "CARGADO",
                    loaded=len(df),
                    rejected=0,
                )
                finish_file(cur, archivo_id, "CARGADO")

                return {
                    "estado": "CARGADO",
                    "archivo_id": str(archivo_id),
                    "dataset_id": str(dataset_id),
                    "archivo": path.name,
                    "hojas": data["hojas"],
                    "filas_total": len(df),
                    "fecha_min": str(data["fecha_min"]),
                    "fecha_max": str(data["fecha_max"]),
                }
