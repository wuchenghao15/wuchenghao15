# -*- coding: utf-8 -*-

import logging
import logging.handlers
import os
from datetime import datetime

log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10485760,
            backupCount=5,
            encoding='utf-8'
        )
    ])

logger_ai = logging.getLogger('ai')
logger_ai.setLevel(logging.INFO)

logger_db = logging.getLogger('database')
logger_db.setLevel(logging.INFO)

logger_api = logging.getLogger('api')
logger_api.setLevel(logging.INFO)
