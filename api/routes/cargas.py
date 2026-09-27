from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil

from fastapi import APIRouter, File, UploadFile, HTTPException

from src.loaders import (
    cargar_archivo_usos,
    cargar_dia_tipo,
)

router = APIRouter()

def _save_temp(file: UploadFile) -> Path:
    suffix = Path(file.filename or "").suffix or ".xlsx"

    with NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as tmp:
        shutil.copyfileobj(
            file.file,
            tmp,
        )
        return Path(tmp.name)

@router.post("/usos")
def upload_usos(
    file: UploadFile = File(...),
):
    path = _save_temp(file)

    try:
        return cargar_archivo_usos(path)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    finally:
        path.unlink(missing_ok=True)

@router.post("/dia-tipo")
def upload_dia_tipo(
    file: UploadFile = File(...),
    sheet: str = "Hoja2",
):
    path = _save_temp(file)

    try:
        return cargar_dia_tipo(
            path,
            sheet_name=sheet,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    finally:
        path.unlink(missing_ok=True)
