import pandas as pd

from logger.logger import get_logger
from transformation.normalization import normalize_transactions


lg = get_logger()


def transform_transactions(
    atm_df: pd.DataFrame,
    ach_df: pd.DataFrame,
    api_df: pd.DataFrame
) -> pd.DataFrame:

    lg.info(
        "Iniciando transformación de transacciones"
    )

    # ==========================================================
    # COPIAS
    # ==========================================================

    atm_df = atm_df.copy()
    ach_df = ach_df.copy()
    api_df = api_df.copy()

    lg.info(
        f"Registros recibidos - "
        f"ATM: {len(atm_df)}, "
        f"ACH: {len(ach_df)}, "
        f"API: {len(api_df)}"
    )

    # ==========================================================
    # SOURCE
    # ==========================================================

    atm_df["source"] = "ATM"
    ach_df["source"] = "ACH"
    api_df["source"] = "API"

    lg.info(
        "Source asignado correctamente"
    )

    # ==========================================================
    # CHANNEL
    # ==========================================================

    atm_df["channel_code"] = "ATM"
    ach_df["channel_code"] = "ACH"
    api_df["channel_code"] = "MOBILE"

    lg.info(
        "Channel_code asignado: "
        "ATM → ATM | ACH → ACH | API → MOBILE"
    )

    # ==========================================================
    # UNIFICAR
    # ==========================================================

    df = pd.concat(
        [
            atm_df,
            ach_df,
            api_df
        ],
        ignore_index=True
    )

    lg.info(
        f"Fuentes unificadas: "
        f"{len(df)} registros"
    )

    # ==========================================================
    # NORMALIZAR
    # ==========================================================

    df = normalize_transactions(df)

    # ==========================================================
    # DUPLICADOS
    # ==========================================================

    before = len(df)

    df = df.drop_duplicates(
        subset=["transaction_id"],
        keep="last"
    )

    removed = before - len(df)

    lg.info(
        f"Duplicados eliminados: {removed}"
    )

    # ==========================================================
    # ORDEN FINAL
    # ==========================================================

    columns = [
        "transaction_id",
        "customer_id",
        "account_id",
        "atm_id",
        "transaction_date",
        "transaction_type",
        "amount",
        "currency",
        "status",
        "channel_code",
        "source"
    ]

    columns = [
        column
        for column in columns
        if column in df.columns
    ]

    df = df[columns]

    # ==========================================================
    # RESUMEN
    # ==========================================================

    lg.info(
        f"Columnas finales: {list(df.columns)}"
    )

    lg.info(
        f"Transformación finalizada: "
        f"{len(df)} registros"
    )

    return df