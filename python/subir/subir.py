import os
import pandas as pd

from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# ============================================================
# CONEXIÓN A POSTGRESQL
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


# ============================================================
# RUTA DE LOS CSV
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# CARGAR CSV A GOLD
# ============================================================

def load_csv_to_gold(csv_file, table_name):

    csv_path = os.path.join(BASE_DIR, csv_file)

    print("\n" + "-" * 60)
    print(f"Cargando: {csv_file}")
    print(f"Destino: gold.{table_name}")
    print("-" * 60)

    # --------------------------------------------------------
    # LEER CSV
    # --------------------------------------------------------

    df = pd.read_csv(csv_path)

    print(f"Registros encontrados: {len(df)}")

    # --------------------------------------------------------
    # LIMPIAR NOMBRES DE COLUMNAS
    # --------------------------------------------------------

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    # ========================================================
    # CONVERSIÓN DE TIPOS
    # ========================================================

    # --------------------------------------------------------
    # DIM CUSTOMER
    # --------------------------------------------------------

    if table_name == "dim_customer":

        # birth_date: texto -> fecha
        df["birth_date"] = pd.to_datetime(
            df["birth_date"],
            errors="coerce"
        ).dt.date

        # document_number: número -> texto
        df["document_number"] = (
            df["document_number"]
            .astype("string")
        )

    # --------------------------------------------------------
    # DIM ACCOUNT
    # --------------------------------------------------------

    elif table_name == "dim_account":

        # opening_date: texto -> fecha
        df["opening_date"] = pd.to_datetime(
            df["opening_date"],
            errors="coerce"
        ).dt.date

    # ========================================================
    # LIMPIAR DIMENSIÓN
    # ========================================================

    with engine.begin() as conn:

        conn.execute(
            text(
                f"TRUNCATE TABLE gold.{table_name} "
                f"RESTART IDENTITY CASCADE"
            )
        )

    # ========================================================
    # INSERTAR DATOS
    # ========================================================

    df.to_sql(
        name=table_name,
        con=engine,
        schema="gold",
        if_exists="append",
        index=False
    )

    print(f"✓ gold.{table_name} cargada correctamente")


# ============================================================
# CREAR Y LLENAR DIM_DATE
# ============================================================

def load_dim_date(
    start_date="1985-01-01",
    end_date="2030-12-31"
):

    print("\n" + "=" * 60)
    print("CREANDO Y CARGANDO GOLD.DIM_DATE")
    print("=" * 60)

    # ========================================================
    # CREAR TABLA SI NO EXISTE
    # ========================================================

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS gold.dim_date (
        date_key INTEGER PRIMARY KEY,

        full_date DATE NOT NULL UNIQUE,

        day INTEGER,
        month INTEGER,
        month_name VARCHAR(20),

        quarter INTEGER,
        year INTEGER,

        day_of_week INTEGER,
        day_name VARCHAR(20),

        is_weekend BOOLEAN
    );
    """

    with engine.begin() as conn:

        conn.execute(
            text(create_table_sql)
        )

    print("✓ Tabla gold.dim_date creada/verificada")

    # ========================================================
    # GENERAR FECHAS
    # ========================================================

    dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    df = pd.DataFrame({
        "full_date": dates
    })

    print(f"Fechas generadas: {len(df)}")
    print(f"Desde: {start_date}")
    print(f"Hasta: {end_date}")

    # ========================================================
    # DATE KEY
    # ========================================================

    df["date_key"] = (
        df["full_date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    # ========================================================
    # DÍA
    # ========================================================

    df["day"] = (
        df["full_date"]
        .dt.day
    )

    # ========================================================
    # MES
    # ========================================================

    df["month"] = (
        df["full_date"]
        .dt.month
    )

    # ========================================================
    # NOMBRE DEL MES
    # ========================================================

    month_names = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre"
    }

    df["month_name"] = (
        df["month"]
        .map(month_names)
    )

    # ========================================================
    # TRIMESTRE
    # ========================================================

    df["quarter"] = (
        df["full_date"]
        .dt.quarter
    )

    # ========================================================
    # AÑO
    # ========================================================

    df["year"] = (
        df["full_date"]
        .dt.year
    )

    # ========================================================
    # DÍA DE LA SEMANA
    #
    # Monday = 1
    # Sunday = 7
    # ========================================================

    df["day_of_week"] = (
        df["full_date"]
        .dt.dayofweek + 1
    )

    # ========================================================
    # NOMBRE DEL DÍA
    # ========================================================

    day_names = {
        1: "Lunes",
        2: "Martes",
        3: "Miércoles",
        4: "Jueves",
        5: "Viernes",
        6: "Sábado",
        7: "Domingo"
    }

    df["day_name"] = (
        df["day_of_week"]
        .map(day_names)
    )

    # ========================================================
    # FIN DE SEMANA
    # ========================================================

    df["is_weekend"] = (
        df["day_of_week"] >= 6
    )

    # ========================================================
    # ORDENAR COLUMNAS
    # ========================================================

    df = df[
        [
            "date_key",
            "full_date",
            "day",
            "month",
            "month_name",
            "quarter",
            "year",
            "day_of_week",
            "day_name",
            "is_weekend"
        ]
    ]

    # ========================================================
    # INSERTAR DIM_DATE
    #
    # NO HACEMOS TRUNCATE PORQUE
    # FACT_TRANSACTION TIENE UNA FK A DIM_DATE
    # ========================================================

    with engine.begin() as conn:

        for _, row in df.iterrows():

            conn.execute(
                text("""
                    INSERT INTO gold.dim_date (
                        date_key,
                        full_date,
                        day,
                        month,
                        month_name,
                        quarter,
                        year,
                        day_of_week,
                        day_name,
                        is_weekend
                    )
                    VALUES (
                        :date_key,
                        :full_date,
                        :day,
                        :month,
                        :month_name,
                        :quarter,
                        :year,
                        :day_of_week,
                        :day_name,
                        :is_weekend
                    )
                    ON CONFLICT (date_key) DO NOTHING
                """),
                {
                    "date_key": int(row["date_key"]),
                    "full_date": row["full_date"].date(),
                    "day": int(row["day"]),
                    "month": int(row["month"]),
                    "month_name": row["month_name"],
                    "quarter": int(row["quarter"]),
                    "year": int(row["year"]),
                    "day_of_week": int(row["day_of_week"]),
                    "day_name": row["day_name"],
                    "is_weekend": bool(row["is_weekend"])
                }
            )

    print("✓ gold.dim_date cargada correctamente")


# ============================================================
# CARGAR TODAS LAS DIMENSIONES GOLD
# ============================================================

def load_gold_dimensions():

    print("\n")
    print("=" * 60)
    print("INICIANDO CARGA DE DIMENSIONES GOLD")
    print("=" * 60)

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    load_csv_to_gold(
        "customers.csv",
        "dim_customer"
    )

    # --------------------------------------------------------
    # ACCOUNT
    # --------------------------------------------------------

    load_csv_to_gold(
        "accounts.csv",
        "dim_account"
    )

    # --------------------------------------------------------
    # CHANNEL
    # --------------------------------------------------------

    load_csv_to_gold(
        "channels.csv",
        "dim_channel"
    )

    # --------------------------------------------------------
    # BRANCH
    # --------------------------------------------------------

    load_csv_to_gold(
        "branches.csv",
        "dim_branch"
    )

    # --------------------------------------------------------
    # ATM
    # --------------------------------------------------------

    load_csv_to_gold(
        "atms.csv",
        "dim_atm"
    )

    print("\n✓ Todas las dimensiones de CSV fueron cargadas")


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    # 1. Cargar dimensiones desde CSV
    load_gold_dimensions()

    # 2. Crear y llenar dimensión fecha
    load_dim_date(
        start_date="1985-01-01",
        end_date="2030-12-31"
    )

    print("\n")
    print("=" * 60)
    print("✓ CARGA GOLD COMPLETADA")
    print("=" * 60)