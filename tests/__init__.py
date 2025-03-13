import logging

from xlnumba import logger, VERBOSE_LOG_LEVEL

# create the  verbose logging
logging.addLevelName(VERBOSE_LOG_LEVEL, "VERBOSE")

# Create a console handler
numba_logger = logging.getLogger('numba')
logger.debug("Adding filter to remove numba in test __init__.py body")
numba_logger.setLevel(logging.WARNING)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)
