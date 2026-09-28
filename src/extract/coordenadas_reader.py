from datetime import datetime
from pathlib import Path
import re

import pandas as pd

SHEET_RE = re.compile(r"^PSO\s+(\d{6})$", re.IGNORECASE)

EXPECTED_MAIN_HEADERS = [
    "Código Parada",
    "Tipo",
    "Nombre",
    "Rutas",
    "Latitud",
    "Longitud",
]


def _parse_sheet_date(sheet_name: str):
    match = SHEET_RE.match(sheet_name.strip())
    if not match:
        raise ValueError(
            f"La hoja '{sheet_name}' no cumple el patrón 'PSO YYMMDD'."
        )
    return datetime.strptime(match.group(1), "%y%m%d").date()


def list_coordinate_sheets(path: Path) -> list[str]:
    excel = pd.ExcelFile(path, engine="openpyxl")
    sheets = [
        s for s in excel.sheet_names
        if SHEET_RE.match(s.strip())
    ]
    if not sheets:
        raise ValueError(
            "No se encontraron hojas de coordenadas con patrón 'PSO YYMMDD'."
        )
    return sheets


def read_coordinate_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    path = Path(path)
    fecha_inicio = _parse_sheet_date(sheet_name)

    raw = pd.read_excel(
        path,
        sheet_name=sheet_name,
        header=None,
        engine="openpyxl",
    )

    # Localizar encabezado principal por contenido, no por posición fija.
    header_candidates = raw.index[
        raw.iloc[:, 0].astype("string").str.strip().eq("Código Parada")
    ].tolist()

    if not header_candidates:
        raise ValueError(
            f"No se encontró encabezado 'Código Parada' en '{sheet_name}'."
        )

    header_row = header_candidates[0]

    main_headers = [
        str(v).strip() if not pd.isna(v) else ""
        for v in raw.iloc[header_row, :6].tolist()
    ]

    if main_headers != EXPECTED_MAIN_HEADERS:
        raise ValueError(
            f"Encabezados inesperados en '{sheet_name}': {main_headers}"
        )

    # La fila siguiente desagrega Coordenadas -> Latitud / Longitud.
    #subheader = raw.iloc[header_row + 1, 4:6].astype("string").str.strip().tolist()
    #if subheader != ["Latitud", "Longitud"]:
    #    raise ValueError(
    #        f"Subencabezado de coordenadas inválido en '{sheet_name}': {subheader}"
    #   )

    df = raw.iloc[header_row + 1:, :6].copy()
    df.columns = [
        "codigo_parada",
        "tipo",
        "nombre",
        "rutas",
        "latitud",
        "longitud",
    ]

    # Eliminar solo filas completamente vacías.
    df = df.dropna(how="all").copy()

    # Normalización de campos de texto.
    for col in ["tipo", "nombre", "rutas"]:
        df[col] = df[col].astype("string").str.strip()

    # Código de parada como identificador textual para evitar decimales .0.
    codigo = pd.to_numeric(df["codigo_parada"], errors="coerce")
    if codigo.isna().any():
        raise ValueError(
            f"La hoja '{sheet_name}' contiene códigos de parada inválidos."
        )
    df["codigo_parada"] = codigo.astype("Int64").astype("string")

    # Coordenadas numéricas obligatorias.
    df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
    df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")

    if df[["latitud", "longitud"]].isna().any().any():
        raise ValueError(
            f"La hoja '{sheet_name}' contiene coordenadas nulas o no numéricas."
        )

    invalid_geo = (
        ~df["latitud"].between(-90, 90)
        | ~df["longitud"].between(-180, 180)
    )
    if invalid_geo.any():
        raise ValueError(
            f"La hoja '{sheet_name}' contiene {int(invalid_geo.sum())} "
            "coordenadas fuera de rango geográfico."
        )

    dup = df["codigo_parada"].duplicated(keep=False)
    if dup.any():
        codigos = df.loc[dup, "codigo_parada"].drop_duplicates().head(20).tolist()
        raise ValueError(
            f"La hoja '{sheet_name}' contiene códigos de parada duplicados: {codigos}"
        )

    # Fila real de origen en Excel: +1 por indexación Python y +1 por encabezado.
    first_excel_data_row = header_row + 1
    df.insert(
        0,
        "fila_origen",
        range(first_excel_data_row, first_excel_data_row + len(df)),
    )
    df.insert(0, "nombre_hoja", sheet_name)
    df.insert(1, "fecha_inicio_vigencia", fecha_inicio)

    return df.reset_index(drop=True)


def read_coordinates_workbook(path: Path) -> dict:
    path = Path(path)
    sheets = list_coordinate_sheets(path)

    dataframes = {}
    for sheet in sheets:
        dataframes[sheet] = read_coordinate_sheet(path, sheet)

    unified = pd.concat(dataframes.values(), ignore_index=True)

    return {
        "hojas": sheets,
        "dataframes_hoja": dataframes,
        "dataframe_unificado": unified,
        "fecha_min": unified["fecha_inicio_vigencia"].min(),
        "fecha_max": unified["fecha_inicio_vigencia"].max(),
    }
