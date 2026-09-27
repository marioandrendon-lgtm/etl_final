from datetime import (
    datetime,
    time,
    timedelta,
)

from pathlib import Path
import re

import pandas as pd


# ============================================================
# PATRÓN FECHA PSO
# ============================================================

PSO_DATE_RE = re.compile(
    r"PSO_(\d{6})(?:\D|$)",
    re.IGNORECASE,
)


# ============================================================
# COLUMNAS ESPERADAS
# ============================================================

EXPECTED_COLUMNS = [
    "Fecha de modificación",
    "Día tipo",
    "Designación de tarea vehículo",
    "Subcontratista",
    "Línea",
    "Tipo de viaje corto",
    "Sentido",
    "Número de secuencia de carro",
    "Número de tarea vehículo",
    "desde",
    "hasta",
    "Duración",
    "Punto de inicio",
    "Punto de término",
    "Largo",
    "Número de viaje",
    "Tipo de vehículo del viaje",
    "Secuencia de arcos",
    "Tarea vehículo-línea",
    "NúmSre",
    "Clase de viaje",
    "Descripción de tiempo de recorrido",
    "Variante de línea",
]


# ============================================================
# RENOMBRE DE COLUMNAS
# ============================================================

COLUMN_RENAME = {
    "Fecha de modificación":"fecha_modificacion",
    "Día tipo":"dia_tipo",
    "Designación de tarea vehículo":"designacion_tarea_vehiculo",
    "Subcontratista":"subcontratista",
    "Línea":"linea",
    "Tipo de viaje corto":"tipo_viaje_corto",
    "Sentido":"sentido",
    "Número de secuencia de carro":"numero_secuencia_carro",
    "Número de tarea vehículo":"numero_tarea_vehiculo",
    "desde":"desde",
    "hasta":"hasta",
    "Duración":"duracion",
    "Punto de inicio":"punto_inicio",
    "Punto de término":"punto_termino",
    "Largo":"largo",
    "Número de viaje":"numero_viaje",
    "Tipo de vehículo del viaje":"tipo_vehiculo_viaje",
    "Secuencia de arcos":"secuencia_arcos",
    "Tarea vehículo-línea":"tarea_vehiculo_linea",
    "NúmSre":"numsre",
    "Clase de viaje":"clase_viaje",
    "Descripción de tiempo de recorrido":"descripcion_tiempo_recorrido",
    "Variante de línea":"variante_linea",
}


# ============================================================
# FECHA DE INICIO DE VIGENCIA
# ============================================================

def parse_pso_start_date(
    path: Path
):
    """
    Obtiene la fecha de inicio de vigencia desde el nombre del archivo.

    Ejemplo:
    PSO_260330 -> 2026-03-30
    """

    path = Path(path)

    match = PSO_DATE_RE.search(
        path.name
    )

    if not match:

        raise ValueError(
            f"El nombre '{path.name}' "
            "no contiene el patrón "
            "PSO_YYMMDD."
        )

    raw = match.group(1)

    try:

        return datetime.strptime(
            raw,
            "%y%m%d"
        ).date()

    except ValueError as exc:

        raise ValueError(
            f"La fecha PSO_{raw} "
            "no es válida."
        ) from exc


# ============================================================
# VALIDAR HOJAS DET
# ============================================================

def list_det_sheets(
    path: Path
) -> list[str]:

    excel = pd.ExcelFile(
        path,
        engine="openpyxl",
    )

    hojas_det = [
        sheet
        for sheet in excel.sheet_names
        if sheet.upper().startswith(
            "DET"
        )
    ]

    if len(hojas_det) not in (3, 4):

        raise ValueError(
            "El archivo PSO debe contener "
            "3 o 4 hojas cuyo nombre "
            "inicie por 'DET'. "
            f"Se encontraron {len(hojas_det)}: "
            f"{hojas_det}"
        )

    return hojas_det

# ============================================================
# CONVERTIR HORAS - SE REQUIERE DEFINIR INTERVALOS DE TIEMPO
# En el PSO, desde y hasta pueden representar tiempos operacionales posteriores a las 24:00
# algo normal en programación de transporte por eso se debe manejar como intervalos de tiempo y no como horas del día. 
# ============================================================

def _parse_operational_time(
    value
):

    if value is None:
        return None

    if pd.isna(value):
        return None

    # Excel/openpyxl puede entregar directamente timedelta
    if isinstance(
        value,
        timedelta
    ):
        return value

    if isinstance(
        value,
        pd.Timedelta
    ):
        return value.to_pytimedelta()

    # Hora normal: 05:30:00
    if isinstance(
        value,
        time
    ):
        return timedelta(
            hours=value.hour,
            minutes=value.minute,
            seconds=value.second,
            microseconds=value.microsecond,
        )

    # Timestamp / datetime
    if isinstance(
        value,
        datetime
    ):
        return timedelta(
            hours=value.hour,
            minutes=value.minute,
            seconds=value.second,
            microseconds=value.microsecond,
        )

    if isinstance(
        value,
        pd.Timestamp
    ):
        return timedelta(
            hours=value.hour,
            minutes=value.minute,
            seconds=value.second,
            microseconds=value.microsecond,
        )

    # Excel también puede guardar horas como fracción de día
    if isinstance(
        value,
        (int, float)
    ):
        return timedelta(
            days=float(value)
        )

    text = str(
        value
    ).strip()

    try:

        return pd.to_timedelta(
            text
        ).to_pytimedelta()

    except Exception as exc:

        raise ValueError(
            f"Tiempo operacional inválido: "
            f"{value!r}"
        ) from exc


# ============================================================
# CONVERTIR DURACIÓN
# ============================================================

def _parse_duration(
    value
):

    if value is None:
        return None

    if pd.isna(value):
        return None

    if isinstance(
        value,
        timedelta
    ):
        return value

    if isinstance(
        value,
        pd.Timedelta
    ):
        return value.to_pytimedelta()

    if isinstance(
        value,
        time
    ):

        return timedelta(
            hours=value.hour,
            minutes=value.minute,
            seconds=value.second,
            microseconds=value.microsecond,
        )

    if isinstance(
        value,
        (int, float)
    ):

        return timedelta(
            days=float(value)
        )

    try:

        return pd.to_timedelta(
            str(value).strip()
        ).to_pytimedelta()

    except Exception as exc:

        raise ValueError(
            f"Duración inválida: {value!r}"
        ) from exc


# ============================================================
# LEER UNA HOJA PSO
# ============================================================

def read_pso_sheet(
    path: Path,
    sheet_name: str,
) -> pd.DataFrame:

    df = pd.read_excel(
        path,
        sheet_name=sheet_name,
        engine="openpyxl",
    )

    # --------------------------------------------------------
    # Normalizar nombres de columnas
    # --------------------------------------------------------

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # --------------------------------------------------------
    # Validar columnas
    # --------------------------------------------------------

    missing = [
        column
        for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    extras = [
        column
        for column in df.columns
        if column not in EXPECTED_COLUMNS
    ]

    if missing:

        raise ValueError(
            f"Estructura inválida en "
            f"'{sheet_name}'. "
            f"Faltantes={missing}; "
            f"adicionales={extras}"
        )

    # --------------------------------------------------------
    # Conservar únicamente columnas esperadas
    # --------------------------------------------------------

    df = df[
        EXPECTED_COLUMNS
    ].copy()

    # --------------------------------------------------------
    # Renombrar columnas
    # --------------------------------------------------------

    df = df.rename(
        columns=COLUMN_RENAME
    )

    # --------------------------------------------------------
    # Fecha de modificación
    # --------------------------------------------------------

    df[
        "fecha_modificacion"
    ] = pd.to_datetime(
        df[
            "fecha_modificacion"
        ],
        dayfirst=True,
        errors="coerce",
    )

    invalid_dates = int(
        df[
            "fecha_modificacion"
        ]
        .isna()
        .sum()
    )

    if invalid_dates:

        raise ValueError(
            f"La hoja '{sheet_name}' "
            f"contiene {invalid_dates} "
            "fechas de modificación inválidas."
        )

    # --------------------------------------------------------
    # Día tipo
    # --------------------------------------------------------

    df[
        "dia_tipo"
    ] = (
        df[
            "dia_tipo"
        ]
        .astype("string")
        .str.strip()
    )

    if df[
        "dia_tipo"
    ].isna().any():

        raise ValueError(
            f"La hoja '{sheet_name}' "
            "contiene Día tipo nulo."
        )

    # --------------------------------------------------------
    # Columnas enteras
    # --------------------------------------------------------

    columnas_enteras = [
        "designacion_tarea_vehiculo",
        "numero_secuencia_carro",
        "numero_tarea_vehiculo",
        "numero_viaje",
        "numsre",
    ]

    for column in columnas_enteras:

        df[
            column
        ] = pd.to_numeric(
            df[
                column
            ],
            errors="coerce",
        ).astype(
            "Int64"
        )

    # --------------------------------------------------------
    # Largo
    # --------------------------------------------------------

    df[
        "largo"
    ] = pd.to_numeric(
        df[
            "largo"
        ],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Desde / Hasta
    # --------------------------------------------------------

    df[
    "desde"
        ] = df[
            "desde"
        ].map(
            _parse_operational_time
        )

    df[
    "hasta"
    ] = df[
        "hasta"
    ].map(
        _parse_operational_time
    )

    # --------------------------------------------------------
    # Duración
    # --------------------------------------------------------

    df[
        "duracion"
    ] = df[
        "duracion"
    ].map(
        _parse_duration
    )

    # --------------------------------------------------------
    # Variante de línea
    # --------------------------------------------------------

    df[
        "variante_linea"
    ] = (
        df[
            "variante_linea"
        ]
        .astype("string")
    )

    # --------------------------------------------------------
    # Fila origen
    # --------------------------------------------------------

    df.insert(
        0,
        "fila_origen",
        range(
            2,
            len(df) + 2,
        ),
    )

    # --------------------------------------------------------
    # Hoja origen
    # --------------------------------------------------------

    df.insert(
        0,
        "nombre_hoja",
        sheet_name,
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# LEER WORKBOOK COMPLETO
# ============================================================

def read_pso_workbook(
    path: Path
):

    path = Path(path)

    fecha_inicio = (
        parse_pso_start_date(
            path
        )
    )

    hojas = list_det_sheets(
        path
    )

    dataframes = {}

    columnas_base = None

    for hoja in hojas:

        df = read_pso_sheet(
            path,
            hoja,
        )

        columnas_negocio = [
            column
            for column in df.columns
            if column not in (
                "nombre_hoja",
                "fila_origen",
            )
        ]

        if columnas_base is None:

            columnas_base = (
                columnas_negocio
            )

        elif (
            columnas_negocio
            != columnas_base
        ):

            raise ValueError(
                f"La hoja '{hoja}' "
                "no tiene la misma estructura "
                "de las demás hojas DET."
            )

        dataframes[
            hoja
        ] = df

    # --------------------------------------------------------
    # Unificación de las hojas DET
    # --------------------------------------------------------

    dataframe_unificado = (
        pd.concat(
            list(
                dataframes.values()
            ),
            ignore_index=True,
        )
    )

    dataframe_unificado[
        "fecha_inicio_vigencia"
    ] = fecha_inicio

    return {
        "fecha_inicio_vigencia":
            fecha_inicio,

        "hojas":
            hojas,

        "dataframes_hoja":
            dataframes,

        "dataframe_unificado":
            dataframe_unificado,
    }