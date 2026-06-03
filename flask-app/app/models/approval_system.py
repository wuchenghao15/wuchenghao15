# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审批系统数据模型
支持多级审批、流程定义、状态管理和通知机制
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4


class ApprovalStatus(Enum):
    """审批状态"""
    DRAFT = "draft"              # 草稿
    PENDING = "pending"          # 待审批
    IN_PROGRESS = "in_progress"  # 审批中
    APPROVED = "approved"        # 已批准
    REJECTED = "rejected"        # 已拒绝
    CANCELLED = "cancelled"      # 已取消
    EXPIRED = "expired"          # 已过期


class ApprovalType(Enum):
    """审批类型"""
    CONFIG_CHANGE = "config_change"       # 配置变更
    USER_REGISTRATION = "user_registration" # 用户注册
    CONTENT_REVIEW = "content_review"     # 内容审核
    ORDER_APPROVAL = "order_approval"     # 订单审批
    LEAVE_REQUEST = "leave_request"       # 请假申请
    EXPENSE_CLAIM = "expense_claim"       # 费用报销
    PURCHASE_REQUEST = "purchase_request" # 采购申请
    CUSTOM = "custom"                     # 自定义


class ApprovalPriority(Enum):
    """审批优先级"""
    LOW = "low"       # 低
    MEDIUM = "medium" # 中
    HIGH = "high"     # 高
    URGENT = "urgent" # 紧急


@dataclass
class ApprovalStep:
    """审批步骤"""
    id: str = field(default_factory=lambda: str(uuid4()))
    step_number: int = 0
    role: str = ""           # 审批角色
    user_id: Optional[str] = None  # 指定审批人
    description: str = ""
    required: bool = True    # 是否必须审批
    min_approvers: int = 1   # 最少审批人数
    max_approvers: int = 1   # 最多审批人数
    timeout_hours: int = 24  # 超时时间(小时)
    approved_by: List[str] = field(default_factory=list)
    rejected_by: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, approved, rejected, skipped
    comments: str = ""
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'step_number': self.step_number,
            'role': self.role,
            'user_id': self.user_id,
            'description': self.description,
            'required': self.required,
            'min_approvers': self.min_approvers,
            'max_approvers': self.max_approvers,
            'timeout_hours': self.timeout_hours,
            'approved_by': self.approved_by,
            'rejected_by': self.rejected_by,
            'status': self.status,
            'comments': self.comments,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class ApprovalFlow:
    """审批流程定义"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    approval_type: ApprovalType = ApprovalType.CUSTOM
    steps: List[ApprovalStep] = field(default_factory=list)
    allow_skip: bool = False       # 是否允许跳过
    allow_revoke: bool = True      # 是否允许撤回
    allow_delegate: bool = False   # 是否允许委托
    auto_expire_hours: int = 168   # 自动过期时间(小时)
    notify_on_status_change: bool = True
    notify_on_timeout: bool = True
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'approval_type': self.approval_type.value,
            'steps': [step.to_dict() for step in self.steps],
            'allow_skip': self.allow_skip,
            'allow_revoke': self.allow_revoke,
            'allow_delegate': self.allow_delegate,
            'auto_expire_hours': self.auto_expire_hours,
            'notify_on_status_change': self.notify_on_status_change,
            'notify_on_timeout': self.notify_on_timeout,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class ApprovalRequest:
    """审批请求"""
    id: str = field(default_factory=lambda: str(uuid4()))
    flow_id: str = ""
    flow_name: str = ""
    approval_type: ApprovalType = ApprovalType.CUSTOM
    title: str = ""
    description: str = ""
    data: Dict[str, Any] = field(default_factory=dict)  # 请求数据
    priority: ApprovalPriority = ApprovalPriority.MEDIUM
    requester_id: str = ""
    requester_name: str = ""
    requester_role: str = ""
    status: ApprovalStatus = ApprovalStatus.DRAFT
    current_step_index: int = 0
    steps: List[ApprovalStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'flow_id': self.flow_id,
            'flow_name': self.flow_name,
            'approval_type': self.approval_type.value,
            'title': self.title,
            'description': self.description,
            'data': self.data,
            'priority': self.priority.value,
            'requester_id': self.requester_id,
            'requester_name': self.requester_name,
            'requester_role': self.requester_role,
            'status': self.status.value,
            'current_step_index': self.current_step_index,
            'steps': [step.to_dict() for step in self.steps],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoked_by': self.revoked_by
        }


@dataclass
class ApprovalNotification:
    """审批通知"""
    id: str = field(default_factory=lambda: str(uuid4()))
    request_id: str = ""
    user_id: str = ""
    type: str = ""  # created, assigned, approved, rejected, cancelled, expired, reminder
    title: str = ""
    message: str = ""
    read: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'request_id': self.request_id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'read': self.read,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None
        }


@dataclass
class ApprovalDelegate:
    """审批委托"""
    id: str = field(default_factory=lambda: str(uuid4()))
    delegator_id: str = ""      # 委托人
    delegatee_id: str = ""      # 被委托人
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    approval_types: List[str] = field(default_factory=list)  # 委托的审批类型
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'delegator_id': self.delegator_id,
            'delegatee_id': self.delegatee_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'approval_types': self.approval_types,
            'active': self.active,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ApprovalStats:
    """审批统计"""
    total_requests: int = 0
    pending_requests: int = 0
    approved_requests: int = 0
    rejected_requests: int = 0
    cancelled_requests: int = 0
    avg_processing_time_hours: float = 0.0
    approval_rate: float = 0.0
    pending_by_type: Dict[str, int] = field(default_factory=dict)
    pending_by_priority: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'total_requests': self.total_requests,
            'pending_requests': self.pending_requests,
            'approved_requests': self.approved_requests,
            'rejected_requests': self.rejected_requests,
            'cancelled_requests': self.cancelled_requests,
            'avg_processing_time_hours': self.avg_processing_time_hours,
            'approval_rate': self.approval_rate,
            'pending_by_type': self.pending_by_type,
            'pending_by_priority': self.pending_by_priority
        }
