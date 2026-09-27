from dataclasses import dataclass
import os

from dotenv import load_dotenv


# ============================================================
# CARGAR VARIABLES DEL ARCHIVO .env
# ============================================================

load_dotenv()


# ============================================================
# CLASE DE CONFIGURACIÓN
# ============================================================

@dataclass(frozen=True)
class Settings:

    # --------------------------------------------------------
    # Supabase
    # --------------------------------------------------------
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str
    supabase_storage_bucket: str

    # --------------------------------------------------------
    # ETL
    # --------------------------------------------------------
    etl_batch_size: int

    # --------------------------------------------------------
    # PostgreSQL directo
    # --------------------------------------------------------
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    # Pool
    db_pool_min: int
    db_pool_max: int

# ============================================================
# CARGAR CONFIGURACIÓN
# ============================================================

def load_settings() -> Settings:

     # ========================================================
    # Supabase
    # ========================================================

    supabase_url = os.getenv("SUPABASE_URL")

    supabase_key = os.getenv("SUPABASE_KEY")

    supabase_service_role_key = os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY"
    )

    supabase_storage_bucket = os.getenv(
        "SUPABASE_STORAGE_BUCKET",
        "etl-raw"
    )

    # ========================================================
    # ETL
    # ========================================================

    etl_batch_size = int(
        os.getenv(
            "ETL_BATCH_SIZE",
            "1000"
        )
    )

    # ========================================================
    # PostgreSQL
    # ========================================================

    db_host = os.getenv("DB_HOST")

    db_port = int(
        os.getenv(
            "DB_PORT",
            "5432"
        )
    )

    db_name = os.getenv(
        "DB_NAME",
        "postgres"
    )

    db_user = os.getenv("DB_USER")

    db_password = os.getenv("DB_PASSWORD")

    db_pool_min = int(
        os.getenv(
            "DB_POOL_MIN",
            "0"
        )
    )

    db_pool_max = int(
        os.getenv(
            "DB_POOL_MAX",
            "5"
        )
    )

    # ========================================================
    # Validaciones
    # ========================================================

    if not supabase_url:
        raise RuntimeError(
            "Falta SUPABASE_URL en el archivo .env"
        )

    if not supabase_key:
        raise RuntimeError(
            "Falta SUPABASE_KEY en el archivo .env"
        )

    if not supabase_service_role_key:
        raise RuntimeError(
            "Falta SUPABASE_SERVICE_ROLE_KEY en el archivo .env"
        )

    if not db_host:
        raise RuntimeError(
            "Falta DB_HOST en el archivo .env"
        )

    if not db_user:
        raise RuntimeError(
            "Falta DB_USER en el archivo .env"
        )

    if not db_password:
        raise RuntimeError(
            "Falta DB_PASSWORD en el archivo .env"
        )

    if etl_batch_size <= 0:
        raise RuntimeError(
            "ETL_BATCH_SIZE debe ser mayor que cero."
        )

    if db_pool_min < 0:
        raise RuntimeError(
            "DB_POOL_MIN no puede ser negativo."
        )

    if db_pool_max < 1:
        raise RuntimeError(
            "DB_POOL_MAX debe ser mayor que cero."
        )

    if db_pool_max < db_pool_min:
        raise RuntimeError(
            "DB_POOL_MAX debe ser mayor o igual a DB_POOL_MIN."
        )

    # ========================================================
    # Retornar configuración
    # ========================================================

    return Settings(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        supabase_service_role_key=supabase_service_role_key,
        supabase_storage_bucket=supabase_storage_bucket,
        etl_batch_size=etl_batch_size,

        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,

        db_pool_min=db_pool_min,
        db_pool_max=db_pool_max,
    )