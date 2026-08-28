import json

import pandas as pd

from conection.database import engine
from logger.logger import get_logger

from sqlalchemy import text

lg = get_logger()


def load_quarantine(
    rejected_df: pd.DataFrame
):
    """
    Carga los registros rechazados
    en quarantine.rejected_transaction.
    """

    if rejected_df.empty:

        lg.info(
            "No existen registros para cargar "
            "en cuarentena"
        )

        return


    try:

        with engine.begin() as connection:

            for _, row in rejected_df.iterrows():
                # ==================================================
                # DATOS PRINCIPALES
                # ==================================================

                transaction_id = row.get(
                    "transaction_id"
                )

                source = row.get(
                    "source"
                )

                rejection_reason = row.get(
                    "rejection_reason"
                )

                # ==================================================
                # RAW DATA
                # ==================================================

                raw_data = row.drop(
                    labels=[
                        "source",
                        "rejection_reason"
                    ],
                    errors="ignore"
                ).to_dict()

                # Convertir NaN/NaT de Pandas a None
                # para generar JSON válido
                raw_data = {
                    key: None if pd.isna(value) else value
                    for key, value in raw_data.items()
                }

                raw_data = json.dumps(
                    raw_data,
                    default=str
                )
                # ==================================================
                # INSERT
                # ==================================================

                connection.execute(
                    text(
                        """
                        INSERT INTO
                        quarantine.rejected_transaction
                        (
                            transaction_id,
                            source,
                            rejection_reason,
                            raw_data
                        )
                        VALUES
                        (
                            :transaction_id,
                            :source,
                            :rejection_reason,
                            CAST(:raw_data AS JSONB)
                        )
                        """
                    ),
                    {
                        "transaction_id": transaction_id,
                        "source": source,
                        "rejection_reason": rejection_reason,
                        "raw_data": raw_data
                    }
                )

        lg.info(
            f"Cuarentena: "
            f"{len(rejected_df)} registros cargados "
            f"en PostgreSQL"
        )

    except Exception as e:

        lg.error(
            f"Error cargando registros "
            f"a cuarentena: {e}"
        )

        raise
