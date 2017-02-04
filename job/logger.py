
DEFAULT_LOGGER_CONFIG = """ {
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%a, %d %b %Y %H:%M:%S"
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },

        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "info.log",
            "maxBytes": 10485760,
            "backupCount": 3,
            "encoding": "utf8"
        },

        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "simple",
            "filename": "errors.log",
            "maxBytes": 10485760,
            "backupCount": 3,
            "encoding": "utf8"
        }
    },

    "loggers": {
         "DEBUG": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": "no"
        },
         "INFO": {
            "level": "INFO",
            "handlers":["console", "info_file_handler" ], 
            "propagate": "no"
        },
         "ERROR": {
            "level": "ERROR",
            "handlers":["console", "error_file_handler" ], 
            "propagate": "no"
        }
    }  
}"""

from collections import MutableMapping

class LoggerFactory(object):
    __config = None
    class Config(MutableMapping):
        def __init__(self, data=DEFAULT_LOGGER_CONFIG):
            from json import loads
            self.__data = loads(data)

        def __len__(self):
            return len(self.__data)

        def __iter__(self):
            return iter(self.__data)

        def __setitem__(self, k, v):
            self.__data[k] = v

        def __delitem__(self, k):
            raise NotImplementedError

        def __getitem__(self, k):
            return self.__data[k]

        def __contains__(self, k):
            return k in self.__data

    def __init__(self):
        self.__config = self.Config()

    @property
    def config(self):
        return self.__config

    def get_logger(self, name, level='INFO'):
        """ Isn't it too wasful?
        """
        import logging.config
        from logging import getLogger

        if level not in self.__config['loggers']:
            level = 'INFO'
        if name not in self.__config['loggers']:
            for ll in ('INFO', 'ERROR', 'DEBUG'):
                logger = self.__config['loggers'][ll].copy() 
                self.__config['loggers'][name] = logger
                logging.config.dictConfig(self.__config)
        logger = getLogger(name)
        logger.setLevel(level)
        return  logger


def main():
    """ Miniamal test.
    """
    factory = LoggerFactory()
    logger  = factory.get_logger(__name__, "DEBUG")
    logger.info("Testing info")
    logger.warning("Testing warning")
    logger.debug("Testing debug") 


if __name__ == "__main__": main()
