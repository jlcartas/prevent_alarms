'''
Created on 16 jul 2025

@author: jlcar
'''

import logging.config
from pathlib import Path
from threading import Lock


class LoggerSingleton:
    _initialized = False
    _lock = Lock()

    BASE_DIR = Path(__file__).resolve().parent.parent
    LOG_DIR = BASE_DIR / "logs"
    CONFIG_PATH = BASE_DIR / "config" / "logging.conf"

    @classmethod
    def setup(cls):
        with cls._lock:
            if cls._initialized:
                return

            cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

            logging.config.fileConfig(
                cls.CONFIG_PATH,
                defaults={"logdir": str(cls.LOG_DIR)},
                disable_existing_loggers=True
            )

            cls._initialized = True

    @classmethod
    def get_logger(cls, name=None):
        cls.setup()
        return logging.getLogger(name or __name__)
