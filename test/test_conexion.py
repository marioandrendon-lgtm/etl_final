from src.database.database import (
    get_connection,
    close_pool,
)


try:

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                select
                    current_database(),
                    current_user,
                    now()
                """
            )

            resultado = cur.fetchone()

            print("CONEXIÓN OK")
            print("Base    :", resultado[0])
            print("Usuario :", resultado[1])
            print("Fecha   :", resultado[2])

finally:

    close_pool()

