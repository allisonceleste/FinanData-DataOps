from pathlib import Path
import logging as lg


def get_logger():

    # --------------------------------------------------
    # Ubicación raíz del proyecto
    # --------------------------------------------------

    BASE_DIR = Path(__file__).resolve().parents[2]

    # Carpeta donde se almacenarán los logs
    LOG_DIR = BASE_DIR / "logs"

    # Crear carpeta si no existe
    LOG_DIR.mkdir(exist_ok=True)

    # --------------------------------------------------
    # Configuración del logger
    # --------------------------------------------------

    logger = lg.getLogger("finandata")

    # Nivel mínimo que registrará
    logger.setLevel(lg.INFO)

    # Evitar agregar múltiples handlers
    if not logger.handlers:

        # Archivo de destino
        log_file = LOG_DIR / "pipeline.log"

        handler = lg.FileHandler(log_file, encoding="utf-8")

        # Formato del log
        formato = lg.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        handler.setFormatter(formato)

        # Asociar handler al logger
        logger.addHandler(handler)

    return logger