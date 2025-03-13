"""
Create logger for library.  A special verbose logger is created which is used for a very
deep debug on statement by statement basis.  This can be helpful, but makes logs very difficult
to read, so generally disabled (level < DEBUG).
"""
import logging

logger = logging.getLogger('xlnumba')

# Verbose logging added for a few statements that generate material amounts of output, that are only occasionally
# useful for debug purposes.
VERBOSE_LOG_LEVEL = int(logging.DEBUG / 2)


def log_verbose(*args, **kwargs):
    logger.log(VERBOSE_LOG_LEVEL, *args, stacklevel=2, **kwargs)


logger.verbose = log_verbose
logger.VERBOSE_LOG_LEVEL = VERBOSE_LOG_LEVEL
