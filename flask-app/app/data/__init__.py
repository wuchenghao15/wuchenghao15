#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据层 - 实现数据与应用分离
提供统一的数据访问接口和数据管理功能
"""

from app.data.dao import BaseDAO, UserDAO, ExamDAO, ApprovalDAO, init_daos
from app.services.data_layer_service import data_layer_service

__all__ = [
    # DAO层
    'BaseDAO',
    'UserDAO',
    'ExamDAO',
    'ApprovalDAO',
    'init_daos',
    
    # 数据服务
    'data_layer_service'
]


def init_data_layer(db_manager_instance):
    """初始化数据层"""
    init_daos(db_manager_instance)
    data_layer_service._ensure_directories()
    from app.utils.logging import logger
    logger.info("数据层初始化完成")
