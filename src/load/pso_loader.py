from pathlib import Path
import hashlib
import pandas as pd

from src.database.database import (
    get_connection,
)

from src.extract.pso_reader import (
    read_pso_workbook,
    parse_pso_start_date,
)

from src.utils.utils import (
    sha256_file,
    sha256_dataframe,
)

from src.quality.audit import (
    find_file_by_hash,
    create_file_record,
    find_content_duplicate,
    create_dataset_record,
    finish_dataset,
    finish_file,
    create_sheet_record,
    finish_sheet,
    recalculate_pso_validity,
)


PSO_HASH_COLUMNS = [
    "fecha_modificacion",
    "dia_tipo",
    "designacion_tarea_vehiculo",
    "subcontratista",
    "linea",
    "tipo_viaje_corto",
    "sentido",
    "numero_secuencia_carro",
    "numero_tarea_vehiculo",
    "desde",
    "hasta",
    "duracion",
    "punto_inicio",
    "punto_termino",
    "largo",
    "numero_viaje",
    "tipo_vehiculo_viaje",
    "secuencia_arcos",
    "tarea_vehiculo_linea",
    "numsre",
    "clase_viaje",
    "descripcion_tiempo_recorrido",
    "variante_linea",
]


def _sheet_hash(df):

    return sha256_dataframe(
        df,
        PSO_HASH_COLUMNS,
    )


def _dataset_hash(
    sheet_hashes: dict
) -> str:

    digest = hashlib.sha256()

    for name in sorted(
        sheet_hashes
    ):

        digest.update(
            name.encode("utf-8")
        )

        digest.update(b"|")

        digest.update(
            sheet_hashes[name]
            .encode("ascii")
        )

        digest.update(b"\n")

    return digest.hexdigest()

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

def _copy_pso_sheet(
    cur,
    archivo_id,
    dataset_id,
    hoja_id,
    fecha_inicio,
    df,
):

    sql = '''
    copy bronze.pso_detalle (
        archivo_id,
        dataset_id,
        hoja_id,
        nombre_hoja,
        fila_origen,
        fecha_inicio_vigencia,
        fecha_modificacion,
        dia_tipo,
        designacion_tarea_vehiculo,
        subcontratista,
        linea,
        tipo_viaje_corto,
        sentido,
        numero_secuencia_carro,
        numero_tarea_vehiculo,
        desde,
        hasta,
        duracion,
        punto_inicio,
        punto_termino,
        largo,
        numero_viaje,
        tipo_vehiculo_viaje,
        secuencia_arcos,
        tarea_vehiculo_linea,
        numsre,
        clase_viaje,
        descripcion_tiempo_recorrido,
        variante_linea
    )
    from stdin
    '''

    with cur.copy(sql) as copy:

        for row in df.itertuples(
            index=False
        ):

            copy.write_row(
                (
                    archivo_id,
                    dataset_id,
                    hoja_id,
                    _db_value(row.nombre_hoja),
                    _db_value(row.fila_origen),
                    fecha_inicio,
                    _db_value(row.fecha_modificacion),
                    _db_value(row.dia_tipo),
                    _db_value(row.designacion_tarea_vehiculo),
                    _db_value(row.subcontratista),
                    _db_value(row.linea),
                    _db_value(row.tipo_viaje_corto),
                    _db_value(row.sentido),
                    _db_value(row.numero_secuencia_carro),
                    _db_value(row.numero_tarea_vehiculo),
                    _db_value(row.desde),
                    _db_value(row.hasta),
                    _db_value(row.duracion),
                    _db_value(row.punto_inicio),
                    _db_value(row.punto_termino),
                    _db_value(row.largo),
                    _db_value(row.numero_viaje),
                    _db_value(row.tipo_vehiculo_viaje),
                    _db_value(row.secuencia_arcos),
                    _db_value(row.tarea_vehiculo_linea),
                    _db_value(row.numsre),
                    _db_value(row.clase_viaje),
                    _db_value(row.descripcion_tiempo_recorrido),
                    _db_value(row.variante_linea),
                )
            )

def cargar_archivo_pso(
    path: Path
) -> dict:

    path = Path(path)

    # ========================================================
    # 1. HASH DEL ARCHIVO FÍSICO
    # ========================================================

    file_hash = sha256_file(
        path
    )

    # ========================================================
    # 2. LEER Y VALIDAR WORKBOOK PSO
    # ========================================================

    pso = read_pso_workbook(
        path
    )

    fecha_inicio = (
        pso[
            "fecha_inicio_vigencia"
        ]
    )

    hojas_df = (
        pso[
            "dataframes_hoja"
        ]
    )

    unificado = (
        pso[
            "dataframe_unificado"
        ]
    )

    # ========================================================
    # 3. HASH DE CADA HOJA
    # ========================================================

    sheet_hashes = {

        nombre: _sheet_hash(df)

        for nombre, df
        in hojas_df.items()
    }

    # ========================================================
    # 4. HASH LÓGICO DEL DATASET PSO
    # ========================================================

    content_hash = (
        _dataset_hash(
            sheet_hashes
        )
    )

    # ========================================================
    # 5. CONEXIÓN
    # ========================================================

    with get_connection() as conn:

        # ----------------------------------------------------
        # Validar duplicado físico
        # ----------------------------------------------------

        with conn.cursor() as cur:

            existing = find_file_by_hash(
                cur,
                file_hash,
            )

        if existing:

            return {
                "estado": "DUPLICADO",
                "motivo": "sha256_archivo",
                "archivo_id": str(
                    existing[0]
                ),
                "archivo": path.name,
            }

        # ====================================================
        # 6. TRANSACCIÓN
        # ====================================================

        with conn.transaction():

            with conn.cursor() as cur:

                # --------------------------------------------
                # REGISTRAR ARCHIVO FÍSICO
                # --------------------------------------------

                archivo_id = (
                    create_file_record(
                        cur=cur,
                        path=path,
                        file_type="PSO",
                        file_hash=file_hash,
                        source_date=fecha_inicio,
                    )
                )

                # --------------------------------------------
                # REGISTRAR INICIO DE VIGENCIA
                # --------------------------------------------

                cur.execute(
                    '''
                    update carga.archivo_etl

                    set fecha_inicio_vigencia = %s

                    where id = %s
                    ''',
                    (
                        fecha_inicio,
                        archivo_id,
                    ),
                )

                # --------------------------------------------
                # VALIDAR DUPLICADO LÓGICO
                # --------------------------------------------

                duplicate_content = (
                    find_content_duplicate(
                        cur,
                        "PSO",
                        content_hash,
                    )
                )

                # --------------------------------------------
                # CREAR DATASET PSO
                # --------------------------------------------

                dataset_id = (
                    create_dataset_record(
                        cur=cur,
                        archivo_id=archivo_id,
                        dataset_type="PSO",
                        content_hash=content_hash,
                        rows_read=len(
                            unificado
                        ),
                        fecha_min=fecha_inicio,
                        fecha_max=fecha_inicio,
                        status=(
                            "DUPLICADO"
                            if duplicate_content
                            else "CARGANDO"
                        ),
                    )
                )

                # --------------------------------------------
                # SI EL DATASET YA EXISTE
                # --------------------------------------------

                if duplicate_content:

                    finish_dataset(
                        cur,
                        dataset_id,
                        "DUPLICADO",
                        loaded=0,
                        rejected=0,
                        message=(
                            "Contenido PSO ya "
                            "cargado previamente."
                        ),
                    )

                    finish_file(
                        cur,
                        archivo_id,
                        "DUPLICADO",
                    )

                    return {
                        "estado": "DUPLICADO",
                        "motivo": (
                            "sha256_contenido"
                        ),
                        "archivo_id": str(
                            archivo_id
                        ),
                        "dataset_id": str(
                            dataset_id
                        ),
                        "archivo": path.name,
                    }

                # --------------------------------------------
                # PROCESAR CADA HOJA DET
                # --------------------------------------------
                
                resultado_hojas = []

                for nombre_hoja, df in (
                    hojas_df.items()
                ):

                    dia_tipos = sorted(
                        str(value)
                        for value
                        in df[
                            "dia_tipo"
                        ]
                        .dropna()
                        .unique()
                    )

                    dia_tipo = (
                        dia_tipos[0]
                        if len(
                            dia_tipos
                        ) == 1
                        else ",".join(
                            dia_tipos
                        )
                    )

                    hoja_id = (
                        create_sheet_record(
                            cur=cur,
                            archivo_id=(
                                archivo_id
                            ),
                            dataset_id=(
                                dataset_id
                            ),
                            sheet_name=(
                                nombre_hoja
                            ),
                            dia_tipo=(
                                dia_tipo
                            ),
                            content_hash=(
                                sheet_hashes[
                                    nombre_hoja
                                ]
                            ),
                            rows_read=len(
                                df
                            ),
                        )
                    )

                    
                    _copy_pso_sheet(
                        cur=cur,
                        archivo_id=archivo_id,
                        dataset_id=dataset_id,
                        hoja_id=hoja_id,
                        fecha_inicio=fecha_inicio,
                        df=df,
                    )

                    finish_sheet(
                        cur=cur,
                        sheet_id=hoja_id,
                        status="CARGADO",
                        loaded=len(df),
                        rejected=0,
                    )

                    resultado_hojas.append(
                        {
                            "hoja": nombre_hoja,
                            "estado": "CARGADO",
                            "filas": len(df),
                            "dia_tipo": dia_tipo,
                        }
                    )
                    
                                    # --------------------------------------------
                # FINALIZAR DATASET PSO
                # --------------------------------------------

                finish_dataset(
                    cur=cur,
                    dataset_id=dataset_id,
                    status="CARGADO",
                    loaded=len(unificado),
                    rejected=0,
                )

                # --------------------------------------------
                # FINALIZAR ARCHIVO
                # --------------------------------------------

                finish_file(
                    cur=cur,
                    archivo_id=archivo_id,
                    status="CARGADO",
                )

                # --------------------------------------------
                # RECALCULAR VIGENCIAS
                # --------------------------------------------

                recalculate_pso_validity(
                    cur
                )

                # --------------------------------------------
                # RETORNAR RESULTADO
                # --------------------------------------------

                return {
                    "estado": "CARGADO",
                    "archivo_id": str(archivo_id),
                    "dataset_id": str(dataset_id),
                    "archivo": path.name,
                    "fecha_inicio_vigencia": str(fecha_inicio),
                    "hojas_det": len(hojas_df),
                    "filas_total": len(unificado),
                    "hojas": resultado_hojas,
                }
                    

def cargar_carpeta_pso(
    folder: Path,
    recursive: bool = False,
) -> dict:

    folder = Path(folder)

    # ========================================================
    # VALIDAR CARPETA
    # ========================================================

    if not folder.exists():

        raise FileNotFoundError(
            f"No existe la carpeta: {folder}"
        )

    if not folder.is_dir():

        raise NotADirectoryError(
            f"La ruta no corresponde "
            f"a una carpeta: {folder}"
        )

    # ========================================================
    # BUSCAR ARCHIVOS EXCEL
    # ========================================================

    if recursive:

        archivos = list(
            folder.rglob("*.xlsx")
        )

    else:

        archivos = list(
            folder.glob("*.xlsx")
        )

    # Ignorar temporales de Excel
    archivos = [
        archivo
        for archivo in archivos
        if not archivo.name.startswith("~$")
    ]

    if not archivos:

        return {
            "estado": "SIN_ARCHIVOS",
            "carpeta": str(folder),
            "archivos_encontrados": 0,
            "resultados": [],
        }

    # ========================================================
    # ORDENAR POR FECHA DE VIGENCIA PSO
    # ========================================================

    archivos_validos = []

    resultados = []

    errores = 0

    for archivo in archivos:

        try:

            fecha_inicio = (
                parse_pso_start_date(
                    archivo
                )
            )

            archivos_validos.append(
                (
                    fecha_inicio,
                    archivo,
                )
            )

        except Exception as exc:

            errores += 1

            resultados.append({
                "estado": "ERROR",
                "archivo": archivo.name,
                "ruta": str(archivo),
                "error": str(exc),
            })

    # Orden cronológico real
    archivos_validos.sort(
        key=lambda item: item[0]
    )

    # ========================================================
    # CONTADORES
    # ========================================================

    cargados = 0
    duplicados = 0
    total_filas = 0

    # ========================================================
    # PROCESAR ARCHIVOS
    # ========================================================

    for numero, (
        fecha_inicio,
        archivo,
    ) in enumerate(
        archivos_validos,
        start=1,
    ):

        print()
        print("=" * 80)

        print(
            f"[{numero}/"
            f"{len(archivos_validos)}] "
            f"Procesando PSO: "
            f"{archivo.name}"
        )

        print(
            f"Inicio vigencia: "
            f"{fecha_inicio}"
        )

        print("=" * 80)

        try:

            resultado = (
                cargar_archivo_pso(
                    archivo
                )
            )

            resultados.append(
                resultado
            )

            estado = resultado.get(
                "estado"
            )

            if estado == "CARGADO":

                cargados += 1

                total_filas += (
                    resultado.get(
                        "filas_total",
                        0,
                    )
                )

            elif estado == "DUPLICADO":

                duplicados += 1

        except Exception as exc:

            errores += 1

            error = {
                "estado": "ERROR",
                "archivo": archivo.name,
                "ruta": str(archivo),
                "error": str(exc),
            }

            resultados.append(
                error
            )

            print(
                f"ERROR PSO: "
                f"{archivo.name}"
            )

            print(
                str(exc)
            )

    # ========================================================
    # RESULTADO
    # ========================================================

    return {
        "estado": (
            "COMPLETADO"
            if errores == 0
            else "COMPLETADO_CON_ERRORES"
        ),
        "carpeta": str(folder),
        "archivos_encontrados": len(
            archivos
        ),
        "archivos_validos": len(
            archivos_validos
        ),
        "archivos_cargados": cargados,
        "archivos_duplicados": duplicados,
        "archivos_error": errores,
        "filas_pso_cargadas": (
            total_filas
        ),
        "resultados": resultados,
    }