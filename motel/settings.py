# controlling nlp pipeline
MERGE_ENTITIES = True
MERGE_NOUN_CHUNKS = False

USE_VERBOSE_DEPENDENCIES = True


# controlling log behavior
LOG_CONFIG = {
    # overall config
    "version" : 1,
    "disable_existing_loggers" : True,
    # simple formatter
    "formatters" : {
        "standard" : {
            "format" : "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    # simple handler
    "handlers" : {
        "default" : {
            "level" : "INFO",
            "formatter" : "standard",
            "class" : "logging.StreamHandler",
            "stream" : "ext://sys.stdout"
        }
    },
    # configure the loggers
    "loggers" : {
        "motel" : {
            "handlers" : ["default"],
            "level" : "INFO",
            "propagate" : False
        }
    }
}