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
    rejection_reason = pd.Series(
        "",
        index=df.index,
        dtype="object"
    )

    # Columnas obligatorias
    for column in required_columns:

        if column not in df.columns:

            raise ValueError(
                f"{source}: falta la columna "
                f"obligatoria '{column}'"
            )

        mask = df[column].isna()

        rejected |= mask

        rejection_reason.loc[
            mask & rejection_reason.eq("")
            ] = f"{column}_null"

    # Columnas específicas
    if source.upper() == "ATM":

        if "atm_id" not in df.columns:

            raise ValueError(
                "ATM: falta la columna 'atm_id'"
            )

        mask = df["atm_id"].isna()

        rejected |= mask

        rejection_reason.loc[
            mask & rejection_reason.eq("")
            ] = "id_atm_nulo"

    elif source.upper() == "ACH":

        if "counterparty_bank" not in df.columns:

            raise ValueError(
                "ACH: falta la columna "
                "'counterparty_bank'"
            )

        mask = df["counterparty_bank"].isna()

        rejected |= mask

        rejection_reason.loc[
            mask & rejection_reason.eq("")
            ] = "counterparty_bank_nulo"

    # ==========================================================
    # DUPLICADOS
    # ==========================================================

    if "transaction_id" in df.columns:
        mask = (
            df["transaction_id"]
            .duplicated(keep=False)
        )

        rejected |= mask

        rejection_reason.loc[
            mask & rejection_reason.eq("")
            ] = "id_transaccion_duplicado"

    # ==========================================================
    # MONTO
    # ==========================================================

    if "amount" in df.columns:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        mask_null = df["amount"].isna()

        mask_negative = df["amount"] < 0

        rejected |= mask_null
        rejected |= mask_negative

        rejection_reason.loc[
            mask_null & rejection_reason.eq("")
            ] = "monto_invalido"

        rejection_reason.loc[
            mask_negative & rejection_reason.eq("")
            ] = "monto_negativo"

    # ==========================================================
    # TIPO DE TRANSACCIÓN
    # ==========================================================

    if "transaction_type" in df.columns:

        # Normalizar temporalmente para validar
        transaction_type = (
            df["transaction_type"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        if source.upper() in ["ATM", "API"]:

            allowed_types = {
                "DEPOSIT",
                "WITHDRAWAL",
                "TRANSFER",
                "PAYMENT"
            }

        elif source.upper() == "ACH":

            allowed_types = {
                "CREDIT",
                "DEBIT",
                "TRANSFER"
            }

        else:

            allowed_types = set()

        mask = ~transaction_type.isin(
            allowed_types
        )

        rejected |= mask

        rejection_reason.loc[
            mask & rejection_reason.eq("")
            ] = "tipo_transaccion_invalido"

        lg.info(
            f"{source}: tipos de transacción inválidos "
            f"detectados: {mask.sum()}"
        )

    # ==========================================================
    # STATUS
    # ==========================================================

    if "status" in df.columns:
        status = (
            df["status"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        allowed_status = {
            "SUCCESS",
            "REJECTED",
            "PENDING",
            "FAILED"
        }

        mask = ~status.isin(
            allowed_status
        )

        rejected |= mask

        rejection_reason.loc[
            mask & rejection_reason.eq("")
            ] = "status_invalido"

        lg.info(
            f"{source}: status inválidos "
            f"detectados: {mask.sum()}"
        )

    # ==========================================================
    # CURRENCY
    # ==========================================================

    if "currency" in df.columns:
        currency = (
            df["currency"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        allowed_currency = {
            "PEN",
            "USD"
        }

        mask = ~currency.isin(
            allowed_currency
        )

        rejected |= mask

        rejection_reason.loc[
            mask & rejection_reason.eq("")
            ] = "moneda_invalida"

        lg.info(
            f"{source}: monedas inválidas "
            f"detectadas: {mask.sum()}"
        )

    # ==========================================================
    # FECHA
    # ==========================================================

    if "transaction_date" in df.columns:

        parsed_dates = pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        )

        mask = parsed_dates.isna()

        rejected |= mask

        rejection_reason.loc[
            mask & rejection_reason.eq("")
            ] = "fecha_transaccion_invalida"

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
    # INFORMACIÓN DE RECHAZO
    # ==========================================================

    rejected_df["source"] = source

    rejected_df["rejection_reason"] = (
        rejection_reason.loc[rejected]
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