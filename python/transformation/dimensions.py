import pandas as pd

from conection.database import engine
from logger.logger import get_logger


lg = get_logger()


def resolve_dimension_keys(
    df: pd.DataFrame
):
    """
    Resuelve las surrogate keys de las dimensiones Gold.

    Retorna:

        fact_ready_df:
            Registros válidos y listos para cargar
            en gold.fact_transaction.

        dimensional_rejected_df:
            Registros que no pudieron resolver
            alguna dimensión obligatoria.
    """



    df = df.copy()

    lg.info(
        f"Registros recibidos: {len(df)}"
    )

    # ==========================================================
    # 1. CUSTOMER
    # ==========================================================

    lg.info("Resolviendo customer_key")

    customers = pd.read_sql(
        """
        SELECT
            customer_key,
            customer_id
        FROM gold.dim_customer
        """,
        engine
    )

    df = df.merge(
        customers,
        on="customer_id",
        how="left"
    )

    customer_missing = df["customer_key"].isna()

    lg.info(
        f"customer_key sin correspondencia: "
        f"{customer_missing.sum()}"
    )

    # ==========================================================
    # 2. ACCOUNT
    # ==========================================================

    lg.info("Resolviendo account_key")

    accounts = pd.read_sql(
        """
        SELECT
            account_key,
            account_id
        FROM gold.dim_account
        """,
        engine
    )

    df = df.merge(
        accounts,
        on="account_id",
        how="left"
    )

    account_missing = df["account_key"].isna()

    lg.info(
        f"account_key sin correspondencia: "
        f"{account_missing.sum()}"
    )

    # ==========================================================
    # 3. DATE
    # ==========================================================

    lg.info("Resolviendo date_key")

    dates = pd.read_sql(
        """
        SELECT
            date_key,
            full_date
        FROM gold.dim_date
        """,
        engine
    )

    dates["full_date"] = pd.to_datetime(
        dates["full_date"],
        errors="coerce"
    ).dt.date

    df["transaction_full_date"] = (
        pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        ).dt.date
    )

    df = df.merge(
        dates,
        left_on="transaction_full_date",
        right_on="full_date",
        how="left"
    )

    df.drop(
        columns=[
            "transaction_full_date",
            "full_date"
        ],
        inplace=True
    )

    date_missing = df["date_key"].isna()

    lg.info(
        f"date_key sin correspondencia: "
        f"{date_missing.sum()}"
    )

    # ==========================================================
    # 4. CHANNEL
    # ==========================================================

    lg.info("Resolviendo channel_key")

    channels = pd.read_sql(
        """
        SELECT
            channel_key,
            channel_code
        FROM gold.dim_channel
        """,
        engine
    )

    df = df.merge(
        channels,
        on="channel_code",
        how="left"
    )

    channel_missing = df["channel_key"].isna()

    lg.info(
        f"channel_key sin correspondencia: "
        f"{channel_missing.sum()}"
    )

    # ==========================================================
    # 5. ATM
    # ==========================================================

    lg.info("Resolviendo atm_key")

    atms = pd.read_sql(
        """
        SELECT
            atm_key,
            atm_id,
            branch_id
        FROM gold.dim_atm
        """,
        engine
    )

    df = df.merge(
        atms,
        on="atm_id",
        how="left"
    )

    # Solo es error cuando existe atm_id
    # pero no existe en dim_atm.

    atm_missing = (
        df["atm_id"].notna()
        & df["atm_key"].isna()
    )

    lg.info(
        f"atm_key sin correspondencia "
        f"cuando existe atm_id: "
        f"{atm_missing.sum()}"
    )

    # ==========================================================
    # 6. BRANCH
    # ==========================================================

    lg.info("Resolviendo branch_key")

    branches = pd.read_sql(
        """
        SELECT
            branch_key,
            branch_id
        FROM gold.dim_branch
        """,
        engine
    )

    df = df.merge(
        branches,
        on="branch_id",
        how="left"
    )

    # Solo es error cuando existe branch_id
    # pero no existe en dim_branch.

    branch_missing = (
        df["branch_id"].notna()
        & df["branch_key"].isna()
    )

    lg.info(
        f"branch_key sin correspondencia "
        f"cuando existe branch_id: "
        f"{branch_missing.sum()}"
    )

    # ==========================================================
    # 7. IDENTIFICAR REGISTROS INVÁLIDOS
    # ==========================================================

    lg.info(
        "Validando integridad referencial "
        "de las dimensiones"
    )

    # Estas dimensiones son obligatorias
    required_dimension_errors = (
        customer_missing
        | account_missing
        | date_missing
        | channel_missing
    )

    # ATM y branch son opcionales dependiendo
    # del tipo de canal/transacción.

    invalid_records = (
        required_dimension_errors
        | atm_missing
        | branch_missing
    )

    # ==========================================================
    # 8. GENERAR REJECTION REASON
    # ==========================================================

    rejection_reason = pd.Series(
        "",
        index=df.index,
        dtype="object"
    )

    rejection_reason.loc[
        customer_missing
        & rejection_reason.eq("")
    ] = "customer_id_no_existe"

    rejection_reason.loc[
        account_missing
        & rejection_reason.eq("")
    ] = "account_id_no_existe"

    rejection_reason.loc[
        date_missing
        & rejection_reason.eq("")
    ] = "fecha_no_existe_dim_date"

    rejection_reason.loc[
        channel_missing
        & rejection_reason.eq("")
    ] = "channel_code_no_existe"

    rejection_reason.loc[
        atm_missing
        & rejection_reason.eq("")
    ] = "atm_id_no_existe"

    rejection_reason.loc[
        branch_missing
        & rejection_reason.eq("")
    ] = "branch_id_no_existe"

    # ==========================================================
    # 9. SEPARAR VÁLIDOS / RECHAZADOS
    # ==========================================================

    dimensional_rejected_df = df.loc[
        invalid_records
    ].copy()

    fact_ready_df = df.loc[
        ~invalid_records
    ].copy()

    # ==========================================================
    # 10. AGREGAR INFORMACIÓN DE RECHAZO
    # ==========================================================

    if not dimensional_rejected_df.empty:

        dimensional_rejected_df["rejection_reason"] = (
            rejection_reason.loc[
                dimensional_rejected_df.index
            ]
        )

        lg.warning(
            f"Registros rechazados por integridad "
            f"dimensional: "
            f"{len(dimensional_rejected_df)}"
        )

    else:

        lg.info(
            "No existen registros rechazados "
            "por integridad dimensional"
        )

    # ==========================================================
    # 11. COLUMNAS PARA FACT_TRANSACTION
    # ==========================================================

    fact_columns = [
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

    fact_columns = [
        column
        for column in fact_columns
        if column in fact_ready_df.columns
    ]

    fact_ready_df = fact_ready_df[
        fact_columns
    ]

    # ==========================================================
    # 12. RESUMEN
    # ==========================================================

    lg.info(
        f"Registros listos para fact_transaction: "
        f"{len(fact_ready_df)}"
    )

    lg.info(
        f"Registros enviados a cuarentena: "
        f"{len(dimensional_rejected_df)}"
    )

    lg.info(
        f"Columnas finales para fact: "
        f"{list(fact_ready_df.columns)}"
    )

    lg.info("=" * 70)
    lg.info(
        "RESOLUCIÓN DE DIMENSIONES FINALIZADA"
    )
    lg.info("=" * 70)

    return (
        fact_ready_df,
        dimensional_rejected_df
    )