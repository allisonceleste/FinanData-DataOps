import pandas as pd
from sqlalchemy import text

from conection.database import engine
from logger.logger import get_logger


lg = get_logger()


def load_fact_transaction(
    df: pd.DataFrame
):
    """
    Carga las transacciones procesadas en gold.fact_transaction.

    Si (transaction_id, source) no existe:
        INSERT

    Si (transaction_id, source) ya existe:
        UPDATE

    Retorna:
        inserted_count
        updated_count
    """


    # ==========================================================
    # VALIDACIÓN INICIAL
    # ==========================================================

    if df is None or df.empty:

        lg.warning(
            "No existen registros para cargar en Gold"
        )

        return 0, 0

    df = df.copy()

    lg.info(
        f"Registros recibidos para carga: {len(df)}"
    )

    # ==========================================================
    # COLUMNAS ESPERADAS
    # ==========================================================

    required_columns = [
        "transaction_id",
        "customer_key",
        "account_key",
        "date_key",
        "channel_key",
        "branch_key",
        "atm_key",
        "transaction_type",
        "amount",
        "currency",
        "status",
        "source"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Faltan columnas requeridas para "
            f"fact_transaction: {missing_columns}"
        )

    lg.info(
        "Estructura del DataFrame validada"
    )

    # ==========================================================
    # ELIMINAR DUPLICADOS
    # ==========================================================

    before = len(df)

    df = df.drop_duplicates(
        subset=[
            "transaction_id",
            "source"
        ],
        keep="last"
    )

    duplicates = before - len(df)

    lg.info(
        f"Duplicados eliminados antes de carga: "
        f"{duplicates}"
    )

    # ==========================================================
    # CONVERSIÓN DE NaN A None
    # ==========================================================

    df = df.astype(object).where(
        pd.notna(df),
        None
    )

    # ==========================================================
    # SQL UPSERT
    # ==========================================================

    sql = text(
        """
        INSERT INTO gold.fact_transaction (
            transaction_id,
            customer_key,
            account_key,
            date_key,
            channel_key,
            branch_key,
            atm_key,
            transaction_type,
            amount,
            currency,
            status,
            source
        )
        VALUES (
            :transaction_id,
            :customer_key,
            :account_key,
            :date_key,
            :channel_key,
            :branch_key,
            :atm_key,
            :transaction_type,
            :amount,
            :currency,
            :status,
            :source
        )

        ON CONFLICT (
            transaction_id,
            source
        )

        DO UPDATE SET

            customer_key = EXCLUDED.customer_key,

            account_key = EXCLUDED.account_key,

            date_key = EXCLUDED.date_key,

            channel_key = EXCLUDED.channel_key,

            branch_key = EXCLUDED.branch_key,

            atm_key = EXCLUDED.atm_key,

            transaction_type = EXCLUDED.transaction_type,

            amount = EXCLUDED.amount,

            currency = EXCLUDED.currency,

            status = EXCLUDED.status,

            update_at = CURRENT_TIMESTAMP
        """
    )

    # ==========================================================
    # CARGA
    # ==========================================================

    inserted_count = 0
    updated_count = 0

    with engine.begin() as connection:

        for _, row in df.iterrows():

            # --------------------------------------------------
            # Verificar si ya existe
            # --------------------------------------------------

            exists_query = text(
                """
                SELECT 1
                FROM gold.fact_transaction
                WHERE transaction_id = :transaction_id
                  AND source = :source
                LIMIT 1
                """
            )

            exists = connection.execute(
                exists_query,
                {
                    "transaction_id": row["transaction_id"],
                    "source": row["source"]
                }
            ).fetchone()

            # --------------------------------------------------
            # Ejecutar UPSERT
            # --------------------------------------------------

            connection.execute(
                sql,
                {
                    "transaction_id": row["transaction_id"],
                    "customer_key": row["customer_key"],
                    "account_key": row["account_key"],
                    "date_key": row["date_key"],
                    "channel_key": row["channel_key"],
                    "branch_key": row["branch_key"],
                    "atm_key": row["atm_key"],
                    "transaction_type": row["transaction_type"],
                    "amount": row["amount"],
                    "currency": row["currency"],
                    "status": row["status"],
                    "source": row["source"]
                }
            )

            if exists:

                updated_count += 1

            else:

                inserted_count += 1

    # ==========================================================
    # LOGS
    # ==========================================================

    lg.info(
        f"Registros insertados: {inserted_count}"
    )

    lg.info(
        f"Registros actualizados: {updated_count}"
    )

    lg.info(
        f"Total procesado: "
        f"{inserted_count + updated_count}"
    )


    return (
        inserted_count,
        updated_count
    )