from pathlib import Path

from src.database.database import get_connection
from src.utils.utils import sha256_file, sha256_dataframe
from src.extract.readers import (
    validate_usos_workbook,
    read_usos,
    read_usos_validador,
    read_dia_tipo,
)
from src.quality.audit import (
    find_file_by_hash,
    create_file_record,
    find_content_duplicate,
    create_dataset_record,
    finish_dataset,
    finish_file,
)

def _copy_usos(cur, dataset_id, df):
    sql = '''
    copy bronze.usos (
        dataset_id,
        fila_origen,
        fecha,
        estacion,
        h1,h2,h3,h4,h5,h6,h7,h8,h9,h10,h11,h12,
        h13,h14,h15,h16,h17,h18,h19,h20,h21,h22,h23
    )
    from stdin
    '''

    with cur.copy(sql) as copy:
        for row in df.itertuples(index=False):
            copy.write_row(
                (
                    dataset_id,
                    row.fila_origen,
                    row.FECHA,
                    row.ESTACION,
                    *[
                        getattr(row, f"H{i}")
                        for i in range(1, 24)
                    ],
                )
            )

def _copy_usos_validador(
    cur,
    dataset_id,
    df,
):
    sql = '''
    copy bronze.usos_validador (
        dataset_id,
        fila_origen,
        fecha,
        estacion,
        veh_id,
        usos_validador
    )
    from stdin
    '''

    with cur.copy(sql) as copy:
        for row in df.itertuples(index=False):
            copy.write_row(
                (
                    dataset_id,
                    row.fila_origen,
                    row.FECHA,
                    row.ESTACION,
                    row.VEH_ID,
                    row.USOS_VALIDADOR,
                )
            )

def _copy_dia_tipo(
    cur,
    dataset_id,
    df,
):
    sql = '''
    copy bronze.dia_tipo (
        dataset_id,
        fila_origen,
        fecha,
        dia_tipo_origen,
        dia_tipo
    )
    from stdin
    '''

    with cur.copy(sql) as copy:
        for row in df.itertuples(index=False):
            copy.write_row(
                (
                    dataset_id,
                    row.fila_origen,
                    row.FECHA,
                    row.DIA_TIPO_ORIGEN,
                    row.DIA_TIPO,
                )
            )

def cargar_archivo_usos(path: Path) -> dict:
    path = Path(path)

    # --------------------------------------------------------
    # 1. Validaciones físicas y de workbook ANTES de escribir
    # --------------------------------------------------------
    validate_usos_workbook(path)

    file_hash = sha256_file(path)

    # --------------------------------------------------------
    # 2. Extraer ambos datasets del MISMO archivo
    # --------------------------------------------------------
    df_usos = read_usos(path)

    df_uv, fecha_uv = read_usos_validador(path)

    # --------------------------------------------------------
    # 3. Validación cruzada de fecha
    # --------------------------------------------------------
    fechas_usos = sorted(
        set(df_usos["FECHA"].dropna())
    )

    # No imponemos que Usos tenga una sola fecha si la fuente
    # no lo garantiza. Sí verificamos que C1 esté incluida
    # cuando Usos contiene información.
    if fechas_usos and fecha_uv not in fechas_usos:
        raise ValueError(
            f"La fecha C1 de UsosValidador ({fecha_uv}) "
            f"no aparece en las fechas de la hoja Usos: "
            f"{fechas_usos[:10]}"
        )

    hash_usos = sha256_dataframe(
        df_usos,
        [
            "FECHA",
            "ESTACION",
            *[f"H{i}" for i in range(1, 24)],
        ],
    )

    hash_uv = sha256_dataframe(
        df_uv,
        [
            "FECHA",
            "ESTACION",
            "VEH_ID",
            "USOS_VALIDADOR",
        ],
    )

    with get_connection() as conn:

        # Primero verificamos duplicado físico fuera de la
        # transacción larga.
        with conn.cursor() as cur:
            existing = find_file_by_hash(
                cur,
                file_hash,
            )

        if existing:
            return {
                "estado": "DUPLICADO",
                "motivo": "sha256_archivo",
                "archivo_id": str(existing[0]),
                "archivo": path.name,
            }

        # ----------------------------------------------------
        # 4. Una sola transacción para:
        # archivo + datasets + Bronze
        # ----------------------------------------------------
        with conn.transaction():
            with conn.cursor() as cur:

                archivo_id = create_file_record(
                    cur=cur,
                    path=path,
                    file_type="RECAUDO_USOS",
                    file_hash=file_hash,
                    source_date=fecha_uv,
                )

                resultado = {
                    "estado": "CARGADO",
                    "archivo_id": str(archivo_id),
                    "archivo": path.name,
                    "fecha_archivo": str(fecha_uv),
                    "datasets": [],
                }

                # ==============================
                # DATASET USOS
                # ==============================
                dup_usos = find_content_duplicate(
                    cur,
                    "USOS",
                    hash_usos,
                )

                dataset_usos_id = create_dataset_record(
                    cur,
                    archivo_id,
                    "USOS",
                    hash_usos,
                    len(df_usos),
                    min(df_usos["FECHA"]) if len(df_usos) else None,
                    max(df_usos["FECHA"]) if len(df_usos) else None,
                    status=(
                        "DUPLICADO"
                        if dup_usos
                        else "CARGANDO"
                    ),
                )

                if dup_usos:
                    finish_dataset(
                        cur,
                        dataset_usos_id,
                        "DUPLICADO",
                        loaded=0,
                        rejected=0,
                        message=(
                            "Contenido USOS ya cargado "
                            f"desde archivo {dup_usos[2]}"
                        ),
                    )

                    resultado["datasets"].append({
                        "tipo": "USOS",
                        "estado": "DUPLICADO",
                        "filas": 0,
                    })

                else:
                    _copy_usos(
                        cur,
                        dataset_usos_id,
                        df_usos,
                    )

                    finish_dataset(
                        cur,
                        dataset_usos_id,
                        "CARGADO",
                        loaded=len(df_usos),
                    )

                    resultado["datasets"].append({
                        "tipo": "USOS",
                        "estado": "CARGADO",
                        "filas": len(df_usos),
                    })

                # ==============================
                # DATASET USOS_VALIDADOR
                # ==============================
                dup_uv = find_content_duplicate(
                    cur,
                    "USOS_VALIDADOR",
                    hash_uv,
                )

                dataset_uv_id = create_dataset_record(
                    cur,
                    archivo_id,
                    "USOS_VALIDADOR",
                    hash_uv,
                    len(df_uv),
                    fecha_uv,
                    fecha_uv,
                    status=(
                        "DUPLICADO"
                        if dup_uv
                        else "CARGANDO"
                    ),
                )

                if dup_uv:
                    finish_dataset(
                        cur,
                        dataset_uv_id,
                        "DUPLICADO",
                        loaded=0,
                        message=(
                            "Contenido USOS_VALIDADOR ya cargado "
                            f"desde archivo {dup_uv[2]}"
                        ),
                    )

                    resultado["datasets"].append({
                        "tipo": "USOS_VALIDADOR",
                        "estado": "DUPLICADO",
                        "filas": 0,
                    })

                else:
                    _copy_usos_validador(
                        cur,
                        dataset_uv_id,
                        df_uv,
                    )

                    finish_dataset(
                        cur,
                        dataset_uv_id,
                        "CARGADO",
                        loaded=len(df_uv),
                    )

                    resultado["datasets"].append({
                        "tipo": "USOS_VALIDADOR",
                        "estado": "CARGADO",
                        "filas": len(df_uv),
                    })

                estados = {
                    d["estado"]
                    for d in resultado["datasets"]
                }

                if estados == {"DUPLICADO"}:
                    estado_archivo = "DUPLICADO"
                    resultado["estado"] = "DUPLICADO"
                elif "DUPLICADO" in estados:
                    estado_archivo = "CARGADO_PARCIAL"
                    resultado["estado"] = "CARGADO_PARCIAL"
                else:
                    estado_archivo = "CARGADO"

                finish_file(
                    cur,
                    archivo_id,
                    estado_archivo,
                )

                return resultado

def cargar_dia_tipo(
    path: Path,
    sheet_name: str = "Hoja2",
) -> dict:

    path = Path(path)

    # ========================================================
    # HASH DEL ARCHIVO FÍSICO
    # ========================================================
    file_hash = sha256_file(path)

    
    df = read_dia_tipo(
        path,
        sheet_name=sheet_name,
    )

    content_hash = sha256_dataframe(
        df,
        [
            "FECHA",
            "DIA_TIPO_ORIGEN",
            "DIA_TIPO",
        ],
    )

    fecha_min = min(df["FECHA"]) if len(df) else None
    fecha_max = max(df["FECHA"]) if len(df) else None

    with get_connection() as conn:

        with conn.cursor() as cur:
            existing = find_file_by_hash(
                cur,
                file_hash,
            )

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
                    cur,
                    path,
                    "DIA_TIPO",
                    file_hash,
                    source_date=None,
                )

                duplicate_content = find_content_duplicate(
                    cur,
                    "DIA_TIPO",
                    content_hash,
                )

                dataset_id = create_dataset_record(
                    cur,
                    archivo_id,
                    "DIA_TIPO",
                    content_hash,
                    len(df),
                    fecha_min,
                    fecha_max,
                    status=(
                        "DUPLICADO"
                        if duplicate_content
                        else "CARGANDO"
                    ),
                )

                if duplicate_content:
                    finish_dataset(
                        cur,
                        dataset_id,
                        "DUPLICADO",
                        message=(
                            "Contenido DIA_TIPO ya cargado "
                            f"desde archivo {duplicate_content[2]}"
                        ),
                    )

                    finish_file(
                        cur,
                        archivo_id,
                        "DUPLICADO",
                    )

                    return {
                        "estado": "DUPLICADO",
                        "motivo": "sha256_contenido",
                        "archivo_id": str(archivo_id),
                        "dataset_id": str(dataset_id),
                        "archivo": path.name,
                    }

                _copy_dia_tipo(
                    cur,
                    dataset_id,
                    df,
                )

                # --------------------------------------------
                # FINALIZAR DATASET
                # --------------------------------------------
                finish_dataset(
                    cur,
                    dataset_id,
                    "CARGADO",
                    loaded=len(df),
                )

                finish_file(
                    cur,
                    archivo_id,
                    "CARGADO",
                )

                # --------------------------------------------
                # RESULTADO FINAL
                # --------------------------------------------
                return {
                    "estado": "CARGADO",
                    "archivo_id": str(archivo_id),
                    "dataset_id": str(dataset_id),
                    "archivo": path.name,
                    "filas": len(df),
                    "fecha_min": str(fecha_min),
                    "fecha_max": str(fecha_max),
                }


def cargar_carpeta_usos(
    folder: Path,
    recursive: bool = False
) -> dict:
    """
    Procesa todos los archivos .xlsx contenidos en una carpeta.

    Cada archivo se procesa individualmente mediante
    cargar_archivo_usos(), conservando:

    - validación de estructura
    - SHA256
    - auditoría
    - control de duplicados
    - transacción PostgreSQL
    - carga USOS
    - carga USOS_VALIDADOR

    Parameters
    ----------
    folder:
        Carpeta que contiene los archivos Excel.

    recursive:
        Si es True busca también en subcarpetas.

    Returns
    -------
    dict:
        Resumen general del procesamiento.
    """

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
            f"La ruta no corresponde a una carpeta: {folder}"
        )

    # ========================================================
    # BUSCAR ARCHIVOS
    # ========================================================

    if recursive:

        archivos = sorted(
            folder.rglob("*.xlsx")
        )

    else:

        archivos = sorted(
            folder.glob("*.xlsx")
        )

    # Ignorar archivos temporales de Excel
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
            "resultados": []
        }

    # ========================================================
    # CONTADORES
    # ========================================================

    total_archivos = len(archivos)

    cargados = 0

    duplicados = 0

    errores = 0

    cargados_parcial = 0

    total_usos = 0

    total_usos_validador = 0

    resultados = []

    # ========================================================
    # PROCESAR ARCHIVOS
    # ========================================================

    for numero, archivo in enumerate(
        archivos,
        start=1
    ):

        print()
        print("=" * 80)

        print(
            f"[{numero}/{total_archivos}] "
            f"Procesando: {archivo.name}"
        )

        print("=" * 80)

        try:

            resultado = cargar_archivo_usos(
                archivo
            )

            resultados.append(
                resultado
            )

            estado = resultado.get(
                "estado"
            )

            # ------------------------------------------------
            # Archivo cargado
            # ------------------------------------------------

            if estado == "CARGADO":

                cargados += 1

            # ------------------------------------------------
            # Carga parcial
            # ------------------------------------------------

            elif estado == "CARGADO_PARCIAL":

                cargados_parcial += 1

            # ------------------------------------------------
            # Duplicado
            # ------------------------------------------------

            elif estado == "DUPLICADO":

                duplicados += 1

            # ------------------------------------------------
            # Contar filas cargadas
            # ------------------------------------------------

            for dataset in resultado.get(
                "datasets",
                []
            ):

                if dataset.get("estado") != "CARGADO":
                    continue

                if dataset.get("tipo") == "USOS":

                    total_usos += dataset.get(
                        "filas",
                        0
                    )

                elif (
                    dataset.get("tipo")
                    == "USOS_VALIDADOR"
                ):

                    total_usos_validador += (
                        dataset.get(
                            "filas",
                            0
                        )
                    )

        except Exception as exc:

            errores += 1

            error = {
                "estado": "ERROR",
                "archivo": archivo.name,
                "ruta": str(archivo),
                "error": str(exc)
            }

            resultados.append(
                error
            )

            print(
                f"ERROR: {archivo.name}"
            )

            print(
                str(exc)
            )

    # ========================================================
    # RESUMEN
    # ========================================================

    return {

        "estado": (
            "COMPLETADO"
            if errores == 0
            else "COMPLETADO_CON_ERRORES"
        ),

        "carpeta": str(folder),

        "archivos_encontrados": (
            total_archivos
        ),

        "archivos_cargados": (
            cargados
        ),

        "archivos_cargados_parcial": (
            cargados_parcial
        ),

        "archivos_duplicados": (
            duplicados
        ),

        "archivos_error": (
            errores
        ),

        "filas_usos_cargadas": (
            total_usos
        ),

        "filas_usos_validador_cargadas": (
            total_usos_validador
        ),

        "resultados": resultados
    }