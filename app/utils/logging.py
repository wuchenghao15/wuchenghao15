#!/usr/bin/env python3
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger('mtscos')
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'mtscos.log'),
        maxBytes=1024 * 1024 * 50,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def get_logger(name):
    return logging.getLogger(f'mtscos.{name}')