import logging
from logging.handlers import RotatingFileHandler
import sys


def configure_app_logger(log_file: str | None = None, level: int = logging.INFO):
    """Configures the root logger with a file and console handler."""
    
    root_logger = logging.getLogger() 

    # Clear any default/lib-added handlers
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    root_logger.setLevel(level)
    file_formatter = logging.Formatter(
        '%(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG) 
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)