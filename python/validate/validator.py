import pandas as pd
import great_expectations as gx

from logger.logger import get_logger


lg = get_logger()


def validate_dataframe(
    df: pd.DataFrame,
    source: str
):
    """
    Valida un DataFrame utilizando Great Expectations.

    Retorna:
        valid_df
        rejected_df
        quality_gate_passed
        rejection_rate

    El umbral del Quality Gate se mantiene
    separado de Great Expectations.
    """

    lg.info(
        f"Iniciando validación {source}: "
        f"{len(df)} registros"
    )

    df = df.copy()

    total = len(df)

    if total == 0:

        lg.warning(
            f"{source}: DataFrame vacío"
        )

        return (
            df.copy(),
            df.copy(),
            True,
            0
        )

    # ==========================================================
    # GREAT EXPECTATIONS
    # ==========================================================

    context = gx.get_context(
        mode="ephemeral"
    )

    datasource = context.data_sources.add_pandas(
        name=f"{source.lower()}_datasource"
    )

    data_asset = datasource.add_dataframe_asset(
        name=f"{source.lower()}_asset"
    )

    batch_definition = (
        data_asset.add_batch_definition_whole_dataframe(
            f"{source.lower()}_batch"
        )
    )

    batch = batch_definition.get_batch(
        batch_parameters={
            "dataframe": df
        }
    )

    # ==========================================================
    # EXPECTATIONS
    # ==========================================================

    required_columns = [
        "transaction_id",
        "account_id",
        "customer_id",
        "transaction_date",
        "transaction_type",
        "amount",
        "currency",
        "status",
    ]

    expectations = []

    # Columnas obligatorias
    for column in required_columns:

        expectations.append(
            gx.expectations.ExpectColumnToExist(
                column=column
            )
        )

    # Columnas específicas
    if source.upper() == "ATM":

        expectations.append(
            gx.expectations.ExpectColumnToExist(
                column="atm_id"
            )
        )

    elif source.upper() == "ACH":

        expectations.append(
            gx.expectations.ExpectColumnToExist(
                column="counterparty_bank"
            )
        )

    # transaction_id no debe tener nulos
    if "transaction_id" in df.columns:

        expectations.append(
            gx.expectations.ExpectColumnValuesToNotBeNull(
                column="transaction_id"
            )
        )

        expectations.append(
            gx.expectations.ExpectColumnValuesToBeUnique(
                column="transaction_id"
            )
        )

    # amount
    if "amount" in df.columns:

        expectations.append(
            gx.expectations.ExpectColumnValuesToNotBeNull(
                column="amount"
            )
        )

        expectations.append(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column="amount",
                min_value=0
            )
        )

    # transaction_date
    if "transaction_date" in df.columns:

        expectations.append(
            gx.expectations.ExpectColumnValuesToNotBeNull(
                column="transaction_date"
            )
        )

    # ==========================================================
    # EJECUTAR EXPECTATIONS
    # ==========================================================

    lg.info(
        f"{source}: ejecutando Great Expectations"
    )

    results = []

    for expectation in expectations:

        try:

            result = batch.validate(
                expectation
            )

            results.append(result)

        except Exception as e:

            lg.error(
                f"{source}: error ejecutando "
                f"expectation: {e}"
            )

            results.append(
                {
                    "success": False
                }
            )

    # ==========================================================
    # IDENTIFICAR REGISTROS RECHAZADOS
    # ==========================================================

    rejected = pd.Series(
        False,
        index=df.index
    )

    # Columnas obligatorias
    for column in required_columns:

        if column not in df.columns:

            raise ValueError(
                f"{source}: falta la columna "
                f"obligatoria '{column}'"
            )

        rejected |= df[column].isna()

    # Columnas específicas
    if source.upper() == "ATM":

        if "atm_id" not in df.columns:

            raise ValueError(
                "ATM: falta la columna 'atm_id'"
            )

        rejected |= df["atm_id"].isna()

    elif source.upper() == "ACH":

        if "counterparty_bank" not in df.columns:

            raise ValueError(
                "ACH: falta la columna "
                "'counterparty_bank'"
            )

        rejected |= df["counterparty_bank"].isna()

    # ==========================================================
    # DUPLICADOS
    # ==========================================================

    if "transaction_id" in df.columns:

        rejected |= (
            df["transaction_id"]
            .duplicated(keep=False)
        )

    # ==========================================================
    # MONTO
    # ==========================================================

    if "amount" in df.columns:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        rejected |= df["amount"].isna()
        rejected |= df["amount"] < 0

    # ==========================================================
    # FECHA
    # ==========================================================

    if "transaction_date" in df.columns:

        parsed_dates = pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        )

        rejected |= parsed_dates.isna()

    # ==========================================================
    # SEPARACIÓN
    # ==========================================================

    valid_df = df.loc[
        ~rejected
    ].copy()

    rejected_df = df.loc[
        rejected
    ].copy()

    rejection_rate = (
        len(rejected_df) / total
        if total > 0
        else 0
    )

    # ==========================================================
    # RESULTADO GREAT EXPECTATIONS
    # ==========================================================

    ge_passed = all(
        (
            result["success"]
            if isinstance(result, dict)
            else result.success
        )
        for result in results
    )

    if ge_passed:

        lg.info(
            f"{source}: Great Expectations "
            f"aprobó las reglas"
        )

    else:

        lg.warning(
            f"{source}: Great Expectations "
            f"detectó incumplimientos"
        )

    # ==========================================================
    # LOGS
    # ==========================================================

    lg.info(
        f"{source}: total={total}"
    )

    lg.info(
        f"{source}: válidos={len(valid_df)}"
    )

    lg.info(
        f"{source}: rechazados={len(rejected_df)}"
    )

    lg.info(
        f"{source}: porcentaje rechazo="
        f"{rejection_rate:.2%}"
    )

    
    return (
        valid_df,
        rejected_df,
        ge_passed,
        rejection_rate
    )