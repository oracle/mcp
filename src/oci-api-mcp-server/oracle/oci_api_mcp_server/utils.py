"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import logging
from logging.handlers import RotatingFileHandler


def initAuditLogger(logger):
    # Create a rotating file handler
    handler = RotatingFileHandler(
        "/tmp/audit.log", maxBytes=5 * 1024 * 1024, backupCount=1
    )
    handler.setLevel(logging.INFO)

    # Create a logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)
