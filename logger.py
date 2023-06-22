from loguru import logger

from config import log_path, level, log_format, rotation, compression


class Logger:
    __instance = None
    __instance_logger: logger = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.__instance_logger = logger
        self.__instance_logger.add(log_path, format=log_format,
                                   level=level, rotation=rotation, compression=compression)

    def __call__(self, *args, **kwargs):
        message = args[0]
        log_level = args[1]

        if log_level == 'Debug':
            self.__instance_logger.debug(message)
        elif log_level == 'Info':
            self.__instance_logger.info(message)
        elif log_level == 'Warning':
            self.__instance_logger.warning(message)
        elif log_level == 'Error':
            self.__instance_logger.warning(message)
        elif log_level == 'Critical':
            self.__instance_logger.critical(message)

    @property
    def get_logger(self):
        return self.__instance_logger
