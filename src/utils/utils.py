from datetime import (date, datetime, timedelta, time,)
from decimal import Decimal
from pathlib import Path
import hashlib
import json
import math
import pandas as pd

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()

def normalize_scalar(value):

    if value is None:return None

    # --------------------------------------------------------
    # Timestamp de pandas
    # --------------------------------------------------------

    if isinstance(value, pd.Timestamp):return value.isoformat()

    # --------------------------------------------------------
    # datetime de Python
    # --------------------------------------------------------

    if isinstance(value, datetime):return value.isoformat()

    # --------------------------------------------------------
    # date de Python
    # --------------------------------------------------------

    if isinstance(value, date):return value.isoformat()

    # --------------------------------------------------------
    # Timedelta de pandas
    # --------------------------------------------------------

    if isinstance(value, pd.Timedelta):value = value.to_pytimedelta()

    # --------------------------------------------------------
    # timedelta de Python
    # --------------------------------------------------------

    if isinstance(value, timedelta):

        return (
            value.days
            * 24
            * 60
            * 60
            * 1_000_000
            +
            value.seconds
            * 1_000_000
            +
            value.microseconds
        )

    # --------------------------------------------------------
    # time de Python
    # --------------------------------------------------------

    if isinstance(value, time):return value.isoformat()

    # --------------------------------------------------------
    # Decimal
    # --------------------------------------------------------

    if isinstance(value, Decimal):return float(value)

    # --------------------------------------------------------
    # NaN
    # --------------------------------------------------------

    if (
        isinstance(value, float)
        and math.isnan(value)
    ):
        return None

    # --------------------------------------------------------
    # NA / NaT de pandas
    # --------------------------------------------------------

    try:

        if pd.isna(value):return None

    except Exception:
        pass

    # --------------------------------------------------------
    # Tipos numpy
    # --------------------------------------------------------

    if hasattr(value, "item"):

        try:
            return value.item()

        except Exception:
            pass

    return value

def sha256_dataframe(df: pd.DataFrame, columns: list[str]) -> str:
    rows = []
    for record in df[columns].to_dict(orient="records"):
        normalized = {
            k: normalize_scalar(v)
            for k, v in record.items()
        }
        rows.append(
            json.dumps(
                normalized,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )

    # El hash lógico no depende del orden físico de las filas.
    rows.sort()

    digest = hashlib.sha256()
    for row in rows:
        digest.update(row.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()
