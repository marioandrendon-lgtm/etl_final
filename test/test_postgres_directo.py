import psycopg

HOST = "aws-0-us-west-2.pooler.supabase.com"
PORT = 5432
DBNAME = "postgres"
USER = "postgres.prirpipdfdcycvdwsyvn"

PASSWORD = "Uao2026etl123"

try:

    with psycopg.connect(
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        user=USER,
        password=PASSWORD,
        sslmode="require",
        connect_timeout=10
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                select
                    current_database(),
                    current_user,
                    now()
                """
            )

            print("CONEXIÓN OK")
            print(cur.fetchone())

except Exception as e:

    print("ERROR")
    print(type(e).__name__)
    print(e)