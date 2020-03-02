import logging
import logging.config
import settings

# when first imported, check settings to see how logging should be enabled
logging.config.dictConfig(settings.LOG_CONFIG)

# wrapper for getting the right logger
def get(filename):
    return logging.getLogger(f"motel.{filename}")