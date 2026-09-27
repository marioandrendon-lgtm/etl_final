from datetime import datetime, timezone
from pathlib import Path

def find_file_by_hash(cur, file_hash: str):
    cur.execute(
        '''
        select id, nombre_archivo, tipo_archivo, estado
        from carga.archivo_etl
        where sha256_archivo = %s
        ''',
        (file_hash,),
    )
    return cur.fetchone()

def create_file_record(
    cur,
    path: Path,
    file_type: str,
    file_hash: str,
    source_date=None,
):
    cur.execute(
        '''
        insert into carga.archivo_etl (
            nombre_archivo,
            tipo_archivo,
            sha256_archivo,
            tamano_bytes,
            fecha_modificacion_origen,
            fecha_archivo,
            ruta_origen,
            estado
        )
        values (
            %s, %s, %s, %s,
            to_timestamp(%s),
            %s, %s, 'CARGANDO'
        )
        returning id
        ''',
        (
            path.name,
            file_type,
            file_hash,
            path.stat().st_size,
            path.stat().st_mtime,
            source_date,
            str(path),
        ),
    )

    return cur.fetchone()[0]

def find_content_duplicate(
    cur,
    dataset_type: str,
    content_hash: str,
):
    cur.execute(
        '''
        select
            d.id,
            d.archivo_id,
            a.nombre_archivo,
            d.estado
        from carga.dataset_etl d
        join carga.archivo_etl a
          on a.id = d.archivo_id
        where d.tipo_dataset = %s
          and d.sha256_contenido = %s
          and d.estado = 'CARGADO'
        order by d.iniciado_en desc
        limit 1
        ''',
        (dataset_type, content_hash),
    )

    return cur.fetchone()

def create_dataset_record(
    cur,
    archivo_id,
    dataset_type: str,
    content_hash: str,
    rows_read: int,
    fecha_min=None,
    fecha_max=None,
    status: str = "CARGANDO",
):
    cur.execute(
        '''
        insert into carga.dataset_etl (
            archivo_id,
            tipo_dataset,
            sha256_contenido,
            estado,
            filas_leidas,
            fecha_min,
            fecha_max
        )
        values (%s,%s,%s,%s,%s,%s,%s)
        returning id
        ''',
        (
            archivo_id,
            dataset_type,
            content_hash,
            status,
            rows_read,
            fecha_min,
            fecha_max,
        ),
    )

    return cur.fetchone()[0]

def finish_dataset(
    cur,
    dataset_id,
    status: str,
    loaded: int = 0,
    rejected: int = 0,
    message=None,
):
    cur.execute(
        '''
        update carga.dataset_etl
        set estado = %s,
            filas_cargadas = %s,
            filas_rechazadas = %s,
            mensaje_error = %s,
            finalizado_en = %s
        where id = %s
        ''',
        (
            status,
            loaded,
            rejected,
            message,
            datetime.now(timezone.utc),
            dataset_id,
        ),
    )

def finish_file(
    cur,
    archivo_id,
    status: str,
    message=None,
):
    cur.execute(
        '''
        update carga.archivo_etl
        set estado = %s,
            mensaje_error = %s,
            finalizado_en = %s
        where id = %s
        ''',
        (
            status,
            message,
            datetime.now(timezone.utc),
            archivo_id,
        ),
    )
