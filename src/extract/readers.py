from pathlib import Path
import pandas as pd

USOS_EXPECTED = [
    "FECHA",
    "ESTACION",
    *[f"H{i}" for i in range(1, 24)],
    "TOTAL_GENERAL",
]

def workbook_sheets(path: Path) -> set[str]:
    return set(pd.ExcelFile(path, engine="openpyxl").sheet_names)

def validate_usos_workbook(path: Path):
    sheets = workbook_sheets(path)
    required = {"Usos", "UsosValidador"}
    missing = required - sheets

    if missing:
        raise ValueError(
            f"El archivo {path.name} no contiene todas las hojas requeridas. "
            f"Faltan: {sorted(missing)}"
        )

def _to_date_series(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(
        series,
        errors="coerce",
        dayfirst=True,
    )
    return parsed.dt.date

def read_usos(path: Path) -> pd.DataFrame:
    df = pd.read_excel(
        path,
        sheet_name="Usos",
        engine="openpyxl",
    )
    df.columns = [str(c).strip() for c in df.columns]

    missing = [
        c for c in USOS_EXPECTED
        if c not in df.columns
    ]
    if missing:
        raise ValueError(
            f"Hoja Usos con estructura incorrecta. Faltan: {missing}"
        )

    df = df[USOS_EXPECTED].copy()
    df["FECHA"] = _to_date_series(df["FECHA"])
    df["ESTACION"] = df["ESTACION"].astype("string").str.strip()

    for i in range(1, 24):
        col = f"H{i}"
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        ).fillna(0)

    df = df.drop(columns=["TOTAL_GENERAL"])

    invalid_dates = df["FECHA"].isna().sum()
    if invalid_dates:
        raise ValueError(
            f"Hoja Usos contiene {invalid_dates} registros con FECHA inválida."
        )

    df = df[
        df["ESTACION"].notna()
        & (df["ESTACION"].str.len() > 0)
    ].copy()

    df.insert(
        0,
        "fila_origen",
        range(2, len(df) + 2),
    )

    return df.reset_index(drop=True)

def _parse_c1_date(value):
    if pd.isna(value):
        raise ValueError(
            "La celda C1 de UsosValidador no contiene fecha."
        )

    if isinstance(value, pd.Timestamp):
        return value.date()

    text = (
        str(value)
        .replace("'", "")
        .replace('"', "")
        .strip()
    )

    parsed = pd.to_datetime(
        text,
        format="%d-%m-%Y",
        errors="coerce",
    )

    if pd.isna(parsed):
        parsed = pd.to_datetime(
            text,
            dayfirst=True,
            errors="coerce",
        )

    if pd.isna(parsed):
        raise ValueError(
            f"No fue posible interpretar C1 como fecha: {value!r}"
        )

    return parsed.date()

def read_usos_validador(path: Path):
    fecha_cell = pd.read_excel(
        path,
        sheet_name="UsosValidador",
        usecols="C",
        nrows=1,
        header=None,
        engine="openpyxl",
    ).iloc[0, 0]

    fecha_archivo = _parse_c1_date(fecha_cell)

    df = pd.read_excel(
        path,
        sheet_name="UsosValidador",
        engine="openpyxl",
    )

    if df.shape[1] < 3:
        raise ValueError(
            "UsosValidador debe contener al menos las columnas A, B y C."
        )

    df = df.iloc[:, :3].copy()
    df.columns = [
        "ESTACION",
        "VEH_ID",
        "USOS_VALIDADOR",
    ]

    df["ESTACION"] = (
        df["ESTACION"]
        .astype("string")
        .str.strip()
    )

    df["VEH_ID"] = (
        df["VEH_ID"]
        .astype("string")
        .str.strip()
    )

    df["USOS_VALIDADOR"] = pd.to_numeric(
        df["USOS_VALIDADOR"],
        errors="coerce",
    )

    df["FECHA"] = fecha_archivo

    # Solo se eliminan filas totalmente vacías.
    df = df[
        ~(
            df["ESTACION"].isna()
            & df["VEH_ID"].isna()
            & df["USOS_VALIDADOR"].isna()
        )
    ].copy()

    df.insert(
        0,
        "fila_origen",
        range(2, len(df) + 2),
    )

    return df.reset_index(drop=True), fecha_archivo

def read_dia_tipo(
    path: Path,
    sheet_name: str = "Hoja2",
) -> pd.DataFrame:

    df = pd.read_excel(
        path,
        sheet_name=sheet_name,
        engine="openpyxl",
    )

    # ========================================================
    # NORMALIZAR NOMBRES DE COLUMNAS
    # ========================================================
    df.columns = [
        str(c).strip()
        for c in df.columns
    ]

    # ========================================================
    # VALIDAR COLUMNAS
    # ========================================================
    required = ["FECHA", "DIA TIPO"]
    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Archivo Día Tipo sin columnas requeridas: {missing}"
        )
    
    # ========================================================
    # CONSERVAR SOLO CAMPOS NECESARIOS
    # ========================================================
    df = df[required].copy()

    df["FECHA"] = _to_date_series(df["FECHA"])

    df["DIA TIPO"] = (
        df["DIA TIPO"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # ========================================================
    # VALIDACIONES DE CALIDAD
    # ========================================================
    if df["FECHA"].isna().any():
        raise ValueError(
            "El archivo Día Tipo contiene FECHA inválida o nula."
        )

    if df["DIA TIPO"].isna().any():
        raise ValueError(
            "El archivo Día Tipo contiene DIA TIPO nulo."
        )

    # ========================================================
    # VALIDAR:
    # UNA FECHA NO PUEDE TENER DOS DIA TIPO DIFERENTES
    # ========================================================
    conflictos = (
        df.groupby("FECHA")["DIA TIPO"]
        .nunique(dropna=True)
        .reset_index(name="cantidad")
        .query("cantidad > 1")
    )

    if not conflictos.empty:
        fechas = ", ".join(
            map(
                str,
                conflicts["FECHA"].tolist()[:20],
            )
        )

        raise ValueError(
            "Una FECHA presenta más de un DIA TIPO. "
            f"Fechas conflictivas: {fechas}"
        )

    # ========================================================
    # ELIMINAR DUPLICADOS EXACTOS
    # ========================================================
    df = df.drop_duplicates(
        subset=["FECHA", "DIA TIPO"],
        keep="first",
    ).copy()

    # ========================================================
    # Conservar origen antes de normalizar catálogo.
    # ========================================================
    df["DIA_TIPO_ORIGEN"] = df["DIA TIPO"]

    
    #Cambiamos el valor de unificar el catálogo de DIA TIPO, para que FEST sea FES, ya que en el catálogo de DIA TIPO solo existe FES.
    df["DIA_TIPO"] = df["DIA TIPO"].replace({
        "FEST": "FES",
    })

    # ========================================================
    # FILA DE ORIGEN
    # ========================================================
    df.insert(
        0,
        "fila_origen",
        range(2, len(df) + 2),
    )

    return df[
        [
            "fila_origen",
            "FECHA",
            "DIA_TIPO_ORIGEN",
            "DIA_TIPO",
        ]
    ].reset_index(drop=True)
