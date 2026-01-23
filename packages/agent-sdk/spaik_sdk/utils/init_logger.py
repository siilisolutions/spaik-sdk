import logging
import os
from typing import cast

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


class CustomLogger(logging.Logger):
    def trace(self, msg, *args, **kwargs):
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, msg, args, **kwargs)


def init_logger(name: str) -> CustomLogger:
    logging.setLoggerClass(CustomLogger)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO if LOG_LEVEL == "INFO" else logging.DEBUG),
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        force=True,  # This ensures we override any existing config
    )
    logger = logging.getLogger(name)
    return cast(CustomLogger, logger)
