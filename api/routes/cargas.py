from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil

from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
)

from src.load.loaders import (
    cargar_archivo_usos,
    cargar_dia_tipo,
)

from src.load.pso_loader import (
    cargar_archivo_pso,
)

from src.load.coordenadas_loader import (
    cargar_coordenadas,
)


router = APIRouter()


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def _save_temp(file: UploadFile) -> Path:
    """
    Guarda temporalmente el archivo recibido por FastAPI.

    El archivo se elimina al finalizar el endpoint.
    """

    suffix = Path(
        file.filename or ""
    ).suffix or ".xlsx"

    with NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as tmp:

        shutil.copyfileobj(
            file.file,
            tmp,
        )

        return Path(
            tmp.name
        )


# ============================================================
# USOS / USOS VALIDADOR
# ============================================================

@router.post("/usos")
def upload_usos(
    file: UploadFile = File(...),
):
    """
    Carga un archivo Excel correspondiente
    a Usos / UsosValidador.
    """

    path = _save_temp(file)

    try:

        resultado = cargar_archivo_usos(
            path
        )

        return resultado

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    finally:

        path.unlink(
            missing_ok=True
        )


# ============================================================
# DÍA TIPO
# ============================================================

@router.post("/dia-tipo")
def upload_dia_tipo(
    file: UploadFile = File(...),
    sheet: str = "Hoja2",
):
    """
    Carga el archivo que contiene
    FECHA y DIA TIPO.
    """

    path = _save_temp(file)

    try:

        resultado = cargar_dia_tipo(
            path,
            sheet_name=sheet,
        )

        return resultado

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    finally:

        path.unlink(
            missing_ok=True
        )


# ============================================================
# PSO
# ============================================================

@router.post("/pso")
def upload_pso(
    file: UploadFile = File(...),
):
    """
    Carga un archivo del
    Plan de Servicios de Operación - PSO.

    El loader existente administra:
    - hash físico del archivo;
    - hash lógico del contenido;
    - control de duplicados;
    - versionamiento de vigencias;
    - auditoría de archivo/dataset/hojas.
    """

    path = _save_temp(file)

    try:

        resultado = cargar_archivo_pso(
            path
        )

        return resultado

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    finally:

        path.unlink(
            missing_ok=True
        )


# ============================================================
# COORDENADAS DE PARADAS
# ============================================================

@router.post("/coordenadas")
def upload_coordenadas(
    file: UploadFile = File(...),
):
    """
    Carga el archivo de coordenadas
    de paradas del SITM-MIO.

    El loader existente administra:
    - hash físico;
    - hash lógico del contenido;
    - control de duplicados;
    - vigencia;
    - auditoría de la carga.
    """

    path = _save_temp(file)

    try:

        resultado = cargar_coordenadas(
            path
        )

        return resultado

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    finally:

        path.unlink(
            missing_ok=True
        )

# ============================================================
# Para agregar funcionalidades futuras
# ============================================================