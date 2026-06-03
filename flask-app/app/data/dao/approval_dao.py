# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审批数据访问对象
"""

from typing import Dict, Optional, Any

from app.data.dao.base_dao import BaseDAO


class ApprovalFlowDAO(BaseDAO):
    """审批流程数据访问对象"""
    
    _table_name = 'approval_flows'
    _primary_key = 'id'
    
    @classmethod
    def list_by_type(cls, approval_type: str, page: int = 1, page_size: int = 20) -> Dict:
        """按类型列出审批流程"""
        return cls.list({'approval_type': approval_type}, page, page_size)


class ApprovalRequestDAO(BaseDAO):
    """审批请求数据访问对象"""
    
    _table_name = 'approval_requests'
    _primary_key = 'id'
    
    @classmethod
    def list_by_flow(cls, flow_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出流程的审批请求"""
        return cls.list({'flow_id': flow_id}, page, page_size)
    
    @classmethod
    def list_by_requester(cls, requester_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出申请人的审批请求"""
        return cls.list({'requester_id': requester_id}, page, page_size)
    
    @classmethod
    def list_by_status(cls, status: str, page: int = 1, page_size: int = 20) -> Dict:
        """按状态列出审批请求"""
        return cls.list({'status': status}, page, page_size)


class ApprovalNotificationDAO(BaseDAO):
    """审批通知数据访问对象"""
    
    _table_name = 'approval_notifications'
    _primary_key = 'id'
    
    @classmethod
    def list_by_user(cls, user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出用户的通知"""
        return cls.list({'user_id': user_id}, page, page_size)
    
    @classmethod
    def list_unread(cls, user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出用户的未读通知"""
        return cls.list({'user_id': user_id, 'read': 0}, page, page_size)


class ApprovalDelegateDAO(BaseDAO):
    """审批委托数据访问对象"""
    
    _table_name = 'approval_delegates'
    _primary_key = 'id'
    
    @classmethod
    def list_by_delegator(cls, delegator_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出委托人的委托"""
        return cls.list({'delegator_id': delegator_id}, page, page_size)
    
    @classmethod
    def list_by_delegatee(cls, delegatee_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出被委托人的委托"""
        return cls.list({'delegatee_id': delegatee_id}, page, page_size)
    
    @classmethod
    def list_active(cls, page: int = 1, page_size: int = 20) -> Dict:
        """列出活跃的委托"""
        return cls.list({'active': 1}, page, page_size)
