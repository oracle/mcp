"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import logging
from logging.handlers import RotatingFileHandler


def initAuditLogger(logger):
    handler = RotatingFileHandler("/tmp/audit.log", maxBytes=5 * 1024 * 1024, backupCount=1)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
