from datetime import date
from fastapi import APIRouter, Query

from src.database import pool

router = APIRouter()

@router.get("/usos-validador-diarios")
def usos_validador_diarios(
    fecha_inicio: date,
    fecha_fin: date,
):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                select
                    fecha,
                    dia_tipo,
                    registros,
                    total_usos_dia
                from consulta.resumen_usos_validador_dia
                where fecha between %s and %s
                order by fecha
                ''',
                (
                    fecha_inicio,
                    fecha_fin,
                ),
            )

            columns = [
                desc.name
                for desc in cur.description
            ]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]

@router.get("/auditoria")
def auditoria(
    limite: int = Query(
        100,
        ge=1,
        le=1000,
    ),
):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                select *
                from consulta.auditoria_archivos
                order by iniciado_en desc
                limit %s
                ''',
                (limite,),
            )

            columns = [
                desc.name
                for desc in cur.description
            ]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]
