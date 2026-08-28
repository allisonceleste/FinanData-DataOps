import pandas as pd
from pathlib import Path

from logger.logger import get_logger


lg = get_logger()


def apply_cdc(
    new_df: pd.DataFrame,
    bronze_file: Path,
    source: str
) -> pd.DataFrame:

    """
    Detecta registros INSERT y UPDATE comparando
    la extracción actual contra el histórico Bronze.

    Key CDC:
        transaction_id
    """

    lg.info(
        f"{source}: iniciando CDC"
    )

   
    # VALIDACIONES
  
    if "transaction_id" not in new_df.columns:

        raise ValueError(
            f"{source}: CDC requiere la columna "
            "'transaction_id'"
        )

    current_df = new_df.copy()

    current_df["transaction_id"] = (
        current_df["transaction_id"]
        .astype(str)
        .str.strip()
    )

    # Eliminar duplicados de la extracción actual
    current_df = current_df.drop_duplicates(
        subset=["transaction_id"],
        keep="last"
    )

  
    # PRIMERA EJECUCIÓN
  
    if not bronze_file.exists():

        lg.info(
            f"{source}: no existe histórico Bronze"
        )

        result = current_df.copy()

        result["_cdc_operation"] = "INSERT"

        lg.info(
            f"{source}: "
            f"{len(result)} registros detectados "
            f"como INSERT"
        )

        return result

    # LEER HISTÓRICO

    old_df = pd.read_csv(
        bronze_file
    )

    if "transaction_id" not in old_df.columns:

        raise ValueError(
            f"{source}: el histórico Bronze "
            "no contiene transaction_id"
        )

    old_df["transaction_id"] = (
        old_df["transaction_id"]
        .astype(str)
        .str.strip()
    )

    # El histórico también debe tener una sola fila
    # por transaction_id
    old_df = old_df.drop_duplicates(
        subset=["transaction_id"],
        keep="last"
    )

    lg.info(
        f"{source}: histórico Bronze: "
        f"{len(old_df)} registros"
    )

    # ÍNDICES

    old_index = old_df.set_index(
        "transaction_id"
    )

    current_index = current_df.set_index(
        "transaction_id"
    )

    # INSERT

    insert_ids = (
        current_index.index
        .difference(old_index.index)
    )

    insert_df = current_df[
        current_df["transaction_id"].isin(
            insert_ids
        )
    ].copy()

    insert_df["_cdc_operation"] = "INSERT"

    # UPDATE

    common_ids = (
        current_index.index
        .intersection(old_index.index)
    )

    updates = []

    # Columnas que realmente se comparan
    compare_columns = [
        column
        for column in current_df.columns
        if column != "transaction_id"
        and column in old_df.columns
    ]

    for transaction_id in common_ids:

        old_row = old_index.loc[
            transaction_id
        ]

        current_row = current_index.loc[
            transaction_id
        ]

        changed = False

        for column in compare_columns:

            old_value = old_row[column]
            current_value = current_row[column]

            # Ambos valores son NaN
            if (
                pd.isna(old_value)
                and pd.isna(current_value)
            ):
                continue

            # Uno es NaN y el otro no
            if (
                pd.isna(old_value)
                or pd.isna(current_value)
            ):
                changed = True
                break

            # Comparación normal
            if str(old_value) != str(current_value):

                changed = True
                break

        if changed:

            row = current_row.to_dict()

            row["_cdc_operation"] = "UPDATE"

            updates.append(row)

    if updates:

        update_df = pd.DataFrame(
            updates
        )

    else:

        update_df = pd.DataFrame(
            columns=current_df.columns.tolist()
            + ["_cdc_operation"]
        )

    # RESULTADO CDC

    result = pd.concat(
        [
            insert_df,
            update_df
        ],
        ignore_index=True
    )

    lg.info(
        f"{source}: CDC "
        f"INSERT={len(insert_df)}, "
        f"UPDATE={len(update_df)}"
    )

    lg.info(
        f"{source}: total cambios detectados="
        f"{len(result)}"
    )

    return result