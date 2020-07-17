# controlling nlp pipeline
MERGE_ENTITIES = True
MERGE_NOUN_CHUNKS = False

USE_VERBOSE_DEPENDENCIES = True

GET_LABELS_FROM_TEXT = True

# weighting neighborhood structure
EDGE_WEIGHTS = {
    "motel" : 1,
    "spacy" : 1
}
EDGE_WEIGHT_DEFAULT = 1

# controlling ensemble learning
CLASSIFICATION_THRESHOLD=0.01
ACCURACY_THRESHOLD=0.7
LEARNING_RATE=10
CLASS_RATIO=0.1

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