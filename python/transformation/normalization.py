import pandas as pd

from logger.logger import get_logger


lg = get_logger()


def normalize_transactions(
    df: pd.DataFrame
) -> pd.DataFrame:

    lg.info(
        "Iniciando normalización de transacciones"
    )

    df = df.copy()

    # ==========================================================
    # NOMBRES DE COLUMNAS
    # ==========================================================

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    lg.info(
        "Nombres de columnas normalizados"
    )

    # ==========================================================
    # TIPOS DE DATOS
    # ==========================================================

    if "transaction_date" in df.columns:

        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        )

        lg.info(
            "transaction_date convertido a datetime"
        )

    if "amount" in df.columns:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        df["amount"] = df["amount"].round(2)

        lg.info(
            "amount convertido a NUMERIC(18,2)"
        )

    # ==========================================================
    # NORMALIZACIÓN DE TEXTO
    # ==========================================================

    text_columns = [
        "transaction_id",
        "customer_id",
        "account_id",
        "atm_id",
        "counterparty_bank",
        "transaction_type",
        "currency",
        "status",
        "channel_code",
        "source"
    ]

    for column in text_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
                .str.upper()
            )

    lg.info(
        "Campos de texto normalizados"
    )

    # ==========================================================
    # MONEDA
    # ==========================================================

    if "currency" in df.columns:

        lg.info(
            "Monedas detectadas: "
            f"{df['currency'].dropna().unique().tolist()}"
        )

    # ==========================================================
    # TIPO DE TRANSACCIÓN
    # ==========================================================

    if "transaction_type" in df.columns:

        lg.info(
            "Tipos de transacción detectados: "
            f"{df['transaction_type'].dropna().unique().tolist()}"
        )

    # ==========================================================
    # STATUS
    # ==========================================================

    if "status" in df.columns:

        lg.info(
            "Estados detectados: "
            f"{df['status'].dropna().unique().tolist()}"
        )

    # ==========================================================
    # RESULTADO
    # ==========================================================

    lg.info(
        f"Normalización finalizada: "
        f"{len(df)} registros"
    )

    return df