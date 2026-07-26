# easyabc2/utils/logging_utils.py
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("easyabc2")
logger.setLevel(logging.DEBUG)  # full level, filtering happens in handlers

#to be used like this:
#from easyabc2.utils.logging_utils import logger
#logger.debug("[MainWindow] Importing MainWindow…")
#logger.info("User opened Preferences dialog.")
#logger.warning("abc2svg path is missing.")
#logger.error("Failed to run xml2abc.")


def setup_logging(app_data_dir: Path, debug_mode: bool):
    """
    Configure logging inside EasyABC2's app data directory.
    Creates a logs/ folder, rotates old logs, and creates a new log file per launch.
    """

    logs_dir = app_data_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Rotate: keep only 10 most recent logs
    existing_logs = sorted(logs_dir.glob("easyabc2-*.log"))
    if len(existing_logs) > 10:
        for old in existing_logs[:-10]:
            try:
                old.unlink()
            except Exception:
                pass

    # Create new log file for this session
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = logs_dir / f"easyabc2-{timestamp}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.info("=== EasyABC2 started ===")
    if debug_mode:
        logger.info("Debug mode enabled.")
    else:
        logger.info("Normal logging mode.")
