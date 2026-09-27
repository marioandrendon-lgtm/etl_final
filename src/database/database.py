# ============================================================
# CONEXIÓN POSTGRESQL - POOL
# ============================================================

from psycopg_pool import ConnectionPool

from config.config import load_settings


settings = load_settings()


# ============================================================
# POOL GLOBAL
# ============================================================

_pool = None


# ============================================================
# CREAR POOL
# ============================================================

def create_pool():
    """
    Crea un nuevo pool de conexiones PostgreSQL.
    """

    return ConnectionPool(
        conninfo="",
        kwargs={
            "host": settings.db_host,
            "port": settings.db_port,
            "dbname": settings.db_name,
            "user": settings.db_user,
            "password": settings.db_password,
            "sslmode": "require",
            "connect_timeout": 10,
        },
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        open=True,
    )


# ============================================================
# OBTENER POOL
# ============================================================

def get_pool():
    """
    Retorna un pool activo.

    Si no existe o fue cerrado, crea uno nuevo.
    """

    global _pool

    if _pool is None or _pool.closed:

        _pool = create_pool()

        # Esperar hasta que el pool tenga conexión disponible.
        _pool.wait(timeout=10)

    return _pool


# ============================================================
# OBTENER CONEXIÓN
# ============================================================

def get_connection():
    """
    Obtiene una conexión del pool activo.
    """

    pool = get_pool()

    return pool.connection()


# ============================================================
# CERRAR POOL
# ============================================================

def close_pool():
    """
    Cierra el pool y elimina la referencia.

    La siguiente llamada a get_connection()
    creará un pool nuevo.
    """

    global _pool

    if _pool is not None:

        if not _pool.closed:
            _pool.close()

        _pool = None