import argparse
from pathlib import Path
# Importa la logica de carga de loaders
from src.load.loaders import (
    cargar_archivo_usos,
    cargar_carpeta_usos,
    cargar_dia_tipo,
)

# Importa la logica de carga de PSO
from src.load.pso_loader import (
    cargar_archivo_pso,
    cargar_carpeta_pso,
)

# Importa la logica de carga de bases de datos
from src.database.database import (
    close_pool,
)

# importa la logica de carga de coordenadas
from src.load.coordenadas_loader import (
    cargar_coordenadas,
)

from reportes.Avance2_ETL_MIO_Silver_Gold_KPI import (
    main as generar_reportes,
)


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "ETL MIO -> PostgreSQL / Supabase"
        )
    )

    # ========================================================
    # SUBCOMANDOS
    # ========================================================

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    # ========================================================
    # COMANDO USOS
    # ========================================================

    parser_usos = subparsers.add_parser(
        "usos",
        help=(
            "Carga archivos con las hojas "
            "Usos y UsosValidador"
        )
    )

    grupo_usos = (
        parser_usos.add_mutually_exclusive_group(
            required=True
        )
    )

    grupo_usos.add_argument(
        "--file",
        type=Path,
        help="Carga un único archivo Excel."
    )

    grupo_usos.add_argument(
        "--folder",
        type=Path,
        help=(
            "Carga todos los archivos .xlsx "
            "de una carpeta."
        )
    )

    parser_usos.add_argument(
        "--recursive",
        action="store_true",
        help=(
            "Busca también archivos Excel "
            "dentro de subcarpetas."
        )
    )

    # ========================================================
    # COMANDO DIA TIPO
    # ========================================================

    parser_dia_tipo = subparsers.add_parser(
        "dia-tipo",
        help=(
            "Carga archivo con información "
            "de Día Tipo."
        )
    )

    parser_dia_tipo.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Archivo Excel de Día Tipo."
    )

    parser_dia_tipo.add_argument(
        "--sheet",
        default="Hoja2",
        help=(
            "Nombre de la hoja que contiene "
            "FECHA y DIA TIPO."
        )
    )

    # ========================================================
    # COMANDO PSO
    # ========================================================

    parser_pso = subparsers.add_parser(
        "pso",
        help=(
            "Carga archivos del Plan de "
            "Servicios de Operación - PSO"
        )
    )

    grupo_pso = (
        parser_pso.add_mutually_exclusive_group(
            required=True
        )
    )

    grupo_pso.add_argument(
        "--file",
        type=Path,
        help="Carga un único archivo PSO."
    )

    grupo_pso.add_argument(
        "--folder",
        type=Path,
        help=(
            "Carga todos los archivos PSO "
            "de una carpeta."
        )
    )

    parser_pso.add_argument(
        "--recursive",
        action="store_true",
        help=(
            "Busca archivos PSO también "
            "en subcarpetas."
        )
    )

    # ========================================================
    # COMANDO COORDENADAS
    # ========================================================

    parser_coordenadas = subparsers.add_parser(
        "coordenadas",
        help=(
            "Carga archivo de coordenadas de paradas."
        )
    )

    parser_coordenadas.add_argument(
        "--file",
        required=True,
        type=Path,
        help=(
            "Archivo Excel COORDENADAS_PARADAS.xlsx."
        )
    )

    # ========================================================
    # COMANDO REPORTES
    # ========================================================

    parser_reportes = subparsers.add_parser(
        "reportes",
        help=(
            "Genera extracts Silver/Gold, "
            "KPIs y gráficos."
        )
    )

    # ========================================================
    # LEER ARGUMENTOS
    # ========================================================

    args = parser.parse_args()

    try:

        # ====================================================
        # USOS
        # ====================================================

        if args.command == "usos":

            if args.file is not None:

                if not args.file.exists():

                    parser.error(
                        f"No existe el archivo: "
                        f"{args.file}"
                    )

                if not args.file.is_file():

                    parser.error(
                        f"La ruta no corresponde "
                        f"a un archivo: "
                        f"{args.file}"
                    )

                resultado = (
                    cargar_archivo_usos(
                        args.file
                    )
                )

            elif args.folder is not None:

                if not args.folder.exists():

                    parser.error(
                        f"No existe la carpeta: "
                        f"{args.folder}"
                    )

                if not args.folder.is_dir():

                    parser.error(
                        f"La ruta no corresponde "
                        f"a una carpeta: "
                        f"{args.folder}"
                    )

                resultado = (
                    cargar_carpeta_usos(
                        folder=args.folder,
                        recursive=args.recursive
                    )
                )

        # ====================================================
        # DIA TIPO
        # ====================================================

        elif args.command == "dia-tipo":

            if not args.file.exists():

                parser.error(
                    f"No existe el archivo: "
                    f"{args.file}"
                )

            resultado = cargar_dia_tipo(
                path=args.file,
                sheet_name=args.sheet
            )

        # ====================================================
        # PSO
        # ====================================================

        elif args.command == "pso":

            if args.file is not None:

                if not args.file.exists():

                    parser.error(
                        f"No existe el archivo: "
                        f"{args.file}"
                    )

                if not args.file.is_file():

                    parser.error(
                        f"La ruta no corresponde "
                        f"a un archivo: "
                        f"{args.file}"
                    )

                resultado = (
                    cargar_archivo_pso(
                        args.file
                    )
                )

            elif args.folder is not None:

                if not args.folder.exists():

                    parser.error(
                        f"No existe la carpeta: "
                        f"{args.folder}"
                    )

                if not args.folder.is_dir():

                    parser.error(
                        f"La ruta no corresponde "
                        f"a una carpeta: "
                        f"{args.folder}"
                    )

                resultado = (
                    cargar_carpeta_pso(
                        folder=args.folder,
                        recursive=args.recursive,
                    )
                )

        # ====================================================
        # COORDENADAS
        # ====================================================
        
        elif args.command == "coordenadas":

            if not args.file.exists():

                parser.error(
                    f"No existe el archivo: "
                    f"{args.file}"
                )

            if not args.file.is_file():

                parser.error(
                    f"La ruta no corresponde aun archivo: "
                    f"{args.file}"
                )

            resultado = cargar_coordenadas(
                args.file
            )

        # ====================================================
        # REPORTES
        # ====================================================
            

        elif args.command == "reportes":

            generar_reportes()

            resultado = {
                "estado": "COMPLETADO",
                "proceso": (
                    "Generación de extracts Silver/Gold, KPIs y gráficos"
                ),
            }

        # ====================================================
        # COMANDO NO SOPORTADO
        # ====================================================

        else:

            raise RuntimeError(
                f"Comando no soportado: "
                f"{args.command}"
            )

        # ====================================================
        # RESULTADO
        # ====================================================

        print()
        print("RESULTADO ETL")
        print("=" * 60)

        print(resultado)

    finally:

        close_pool()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()