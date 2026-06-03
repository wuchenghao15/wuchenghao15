# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据访问对象层 - 实现数据与应用分离
提供统一的数据访问接口
"""

from app.data.dao.base_dao import BaseDAO
from app.data.dao.user_dao import UserDAO
from app.data.dao.exam_dao import ExamDAO
from app.data.dao.approval_dao import ApprovalDAO
import os

__all__ = [
    'BaseDAO',
    'UserDAO',
    'ExamDAO',
    'ApprovalDAO'
]


def init_daos(db_manager_instance):
    """初始化所有DAO"""
    UserDAO.set_db_manager(db_manager_instance)
    ExamDAO.set_db_manager(db_manager_instance)
    ApprovalDAO.set_db_manager(db_manager_instance)
