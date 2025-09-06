import logging
import os
import sys

import logging.handlers

logfile = os.path.join(sys.path[0], "pyshell.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s:%(name)s:%(lineno)s] %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            logfile, mode="a", maxBytes=2**20, backupCount=2, encoding="utf-8"
        ),
    ]
)

logger = logging.getLogger