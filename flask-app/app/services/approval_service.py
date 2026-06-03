#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审批系统服务
支持多级审批流程、状态管理、通知机制和统计分析
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from app.utils.logging import logger
from app.utils.db import db_manager
from app.utils.db_index_manager import index_manager
from app.utils.lock_sync_manager import lock_sync_manager, LockType, synchronized
from app.utils.db_sync_manager import db_sync_manager, ChangeType
from app.models.approval_system import (
    ApprovalStatus, ApprovalType, ApprovalPriority,
    ApprovalStep, ApprovalFlow, ApprovalRequest,
    ApprovalNotification, ApprovalDelegate, ApprovalStats
)


class ApprovalService:
    """审批系统服务类"""

    def __init__(self):
        """初始化审批服务"""
        self._init_tables()
        self._init_indexes()
        self._init_default_flows()
        logger.info("审批系统服务初始化完成")

    def _init_tables(self):
        """初始化数据库表"""
        try:
            # 创建审批流程表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS approval_flows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    approval_type TEXT NOT NULL DEFAULT 'custom',
                    steps TEXT NOT NULL DEFAULT '[]',
                    allow_skip INTEGER NOT NULL DEFAULT 0,
                    allow_revoke INTEGER NOT NULL DEFAULT 1,
                    allow_delegate INTEGER NOT NULL DEFAULT 0,
                    auto_expire_hours INTEGER NOT NULL DEFAULT 168,
                    notify_on_status_change INTEGER NOT NULL DEFAULT 1,
                    notify_on_timeout INTEGER NOT NULL DEFAULT 1,
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 创建审批申请表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS approval_requests (
                    id TEXT PRIMARY KEY,
                    flow_id TEXT NOT NULL,
                    flow_name TEXT NOT NULL,
                    approval_type TEXT NOT NULL DEFAULT 'custom',
                    title TEXT NOT NULL,
                    description TEXT,
                    data TEXT NOT NULL DEFAULT '{}',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    requester_id TEXT NOT NULL,
                    requester_name TEXT NOT NULL,
                    requester_role TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    current_step_index INTEGER NOT NULL DEFAULT 0,
                    steps TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    submitted_at TEXT,
                    completed_at TEXT,
                    expired_at TEXT,
                    revoked_at TEXT,
                    revoked_by TEXT,
                    FOREIGN KEY (flow_id) REFERENCES approval_flows(id)
                )
            """)

            # 创建审批通知表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS approval_notifications (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    read INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    read_at TEXT,
                    FOREIGN KEY (request_id) REFERENCES approval_requests(id)
                )
            """)

            # 创建审批委托表
            db_manager.execute("""
                CREATE TABLE IF NOT EXISTS approval_delegates (
                    id TEXT PRIMARY KEY,
                    delegator_id TEXT NOT NULL,
                    delegatee_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    approval_types TEXT NOT NULL DEFAULT '[]',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            logger.info("审批系统表结构创建完成")
        except Exception as e:
            logger.error(f"创建审批系统表结构失败: {str(e)}")

    def _init_indexes(self):
        """初始化索引"""
        try:
            # 为审批流程表创建索引
            index_manager.create_index('approval_flows', ['approval_type'])
            index_manager.create_index('approval_flows', ['created_by'])

            # 为审批申请表创建索引
            index_manager.create_index('approval_requests', ['flow_id'])
            index_manager.create_index('approval_requests', ['status'])
            index_manager.create_index('approval_requests', ['priority'])
            index_manager.create_index('approval_requests', ['requester_id'])
            index_manager.create_index('approval_requests', ['approval_type'])

            # 为审批通知表创建索引
            index_manager.create_index('approval_notifications', ['user_id'])
            index_manager.create_index('approval_notifications', ['request_id'])
            index_manager.create_index('approval_notifications', ['read'])

            # 为审批委托表创建索引
            index_manager.create_index('approval_delegates', ['delegator_id'])
            index_manager.create_index('approval_delegates', ['delegatee_id'])
            index_manager.create_index('approval_delegates', ['active'])

            logger.info("审批系统索引创建完成")
        except Exception as e:
            logger.warning(f"创建索引失败: {str(e)}")

    def _init_default_flows(self):
        """初始化默认审批流程"""
        try:
            # 检查是否已有流程
            count = db_manager.fetch_scalar("SELECT COUNT(*) FROM approval_flows") or 0
            if count > 0:
                return

            # 创建配置变更审批流程
            config_steps = [
                ApprovalStep(step_number=1, role="admin", description="管理员审批", required=True),
                ApprovalStep(step_number=2, role="super_admin", description="超级管理员审批", required=False)
            ]
            self.create_flow({
                'name': '配置变更审批',
                'description': '系统配置变更的审批流程',
                'approval_type': 'config_change',
                'steps': [s.to_dict() for s in config_steps],
                'allow_skip': False,
                'allow_revoke': True,
                'auto_expire_hours': 24
            })

            # 创建用户注册审批流程
            reg_steps = [
                ApprovalStep(step_number=1, role="moderator", description="审核员审批", required=True)
            ]
            self.create_flow({
                'name': '用户注册审批',
                'description': '新用户注册的审批流程',
                'approval_type': 'user_registration',
                'steps': [s.to_dict() for s in reg_steps],
                'allow_skip': False,
                'allow_revoke': True,
                'auto_expire_hours': 48
            })

            # 创建内容审核流程
            content_steps = [
                ApprovalStep(step_number=1, role="reviewer", description="初审", required=True),
                ApprovalStep(step_number=2, role="editor", description="复审", required=True)
            ]
            self.create_flow({
                'name': '内容审核',
                'description': '内容发布前的审核流程',
                'approval_type': 'content_review',
                'steps': [s.to_dict() for s in content_steps],
                'allow_skip': False,
                'allow_revoke': True,
                'auto_expire_hours': 72
            })

            logger.info("默认审批流程创建完成")
        except Exception as e:
            logger.warning(f"创建默认流程失败: {str(e)}")

    @synchronized(resource='approval_flow_create', lock_type=LockType.WRITE)
    def create_flow(self, flow_data: Dict) -> Optional[str]:
        """创建审批流程"""
        try:
            now = datetime.now(timezone.utc)
            flow = ApprovalFlow(
                id=str(uuid4()),
                name=flow_data.get('name', ''),
                description=flow_data.get('description', ''),
                approval_type=ApprovalType(flow_data.get('approval_type', 'custom')),
                steps=[ApprovalStep(**s) for s in flow_data.get('steps', [])],
                allow_skip=flow_data.get('allow_skip', False),
                allow_revoke=flow_data.get('allow_revoke', True),
                allow_delegate=flow_data.get('allow_delegate', False),
                auto_expire_hours=flow_data.get('auto_expire_hours', 168),
                notify_on_status_change=flow_data.get('notify_on_status_change', True),
                notify_on_timeout=flow_data.get('notify_on_timeout', True),
                created_by=flow_data.get('created_by'),
                created_at=now,
                updated_at=now
            )

            query = """INSERT INTO approval_flows 
                      (id, name, description, approval_type, steps, allow_skip, allow_revoke,
                       allow_delegate, auto_expire_hours, notify_on_status_change, notify_on_timeout,
                       created_by, created_at, updated_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            db_manager.execute(query, (
                flow.id, flow.name, flow.description, flow.approval_type.value,
                json.dumps([s.to_dict() for s in flow.steps]),
                1 if flow.allow_skip else 0,
                1 if flow.allow_revoke else 0,
                1 if flow.allow_delegate else 0,
                flow.auto_expire_hours,
                1 if flow.notify_on_status_change else 0,
                1 if flow.notify_on_timeout else 0,
                flow.created_by,
                flow.created_at.isoformat(),
                flow.updated_at.isoformat()
            ))

            db_sync_manager.track_change('approval_flows', flow.id, ChangeType.INSERT, new_data=flow.to_dict())
            logger.info(f"创建审批流程成功: {flow.id}")
            return flow.id
        except Exception as e:
            logger.error(f"创建审批流程失败: {str(e)}")
            return None

    def get_flow(self, flow_id: str) -> Optional[ApprovalFlow]:
        """获取审批流程"""
        try:
            query = "SELECT * FROM approval_flows WHERE id = ?"
            result = db_manager.fetch_one(query, (flow_id,))
            if not result:
                return None

            if isinstance(result, dict):
                steps = [ApprovalStep(**s) for s in json.loads(result.get('steps', '[]'))]
                return ApprovalFlow(
                    id=result['id'],
                    name=result['name'],
                    description=result.get('description', ''),
                    approval_type=ApprovalType(result.get('approval_type', 'custom')),
                    steps=steps,
                    allow_skip=bool(result.get('allow_skip', 0)),
                    allow_revoke=bool(result.get('allow_revoke', 1)),
                    allow_delegate=bool(result.get('allow_delegate', 0)),
                    auto_expire_hours=result.get('auto_expire_hours', 168),
                    notify_on_status_change=bool(result.get('notify_on_status_change', 1)),
                    notify_on_timeout=bool(result.get('notify_on_timeout', 1)),
                    created_by=result.get('created_by'),
                    created_at=datetime.fromisoformat(result['created_at']),
                    updated_at=datetime.fromisoformat(result['updated_at'])
                )
            else:
                steps = [ApprovalStep(**s) for s in json.loads(result[4] if result[4] else '[]')]
                return ApprovalFlow(
                    id=result[0],
                    name=result[1],
                    description=result[2] if result[2] else '',
                    approval_type=ApprovalType(result[3] if result[3] else 'custom'),
                    steps=steps,
                    allow_skip=bool(result[5] if result[5] else 0),
                    allow_revoke=bool(result[6] if result[6] else 1),
                    allow_delegate=bool(result[7] if result[7] else 0),
                    auto_expire_hours=result[8] if result[8] else 168,
                    notify_on_status_change=bool(result[9] if result[9] else 1),
                    notify_on_timeout=bool(result[10] if result[10] else 1),
                    created_by=result[11],
                    created_at=datetime.fromisoformat(result[12]),
                    updated_at=datetime.fromisoformat(result[13])
                )
        except Exception as e:
            logger.error(f"获取审批流程失败: {str(e)}")
            return None

    def list_flows(self, filters: Optional[Dict] = None, page: int = 1, page_size: int = 20) -> Dict:
        """列出审批流程"""
        try:
            conditions = []
            params = []

            if filters:
                if 'approval_type' in filters:
                    conditions.append("approval_type = ?")
                    params.append(filters['approval_type'])
                if 'created_by' in filters:
                    conditions.append("created_by = ?")
                    params.append(filters['created_by'])

            where_str = " AND ".join(conditions) if conditions else "1=1"

            count_query = f"SELECT COUNT(*) FROM approval_flows WHERE {where_str}"
            total = db_manager.fetch_scalar(count_query, tuple(params)) or 0

            offset = (page - 1) * page_size
            query = f"SELECT * FROM approval_flows WHERE {where_str} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            rows = db_manager.fetch_all(query, tuple(params))
            flows = []

            for row in rows:
                if isinstance(row, dict):
                    steps = [ApprovalStep(**s) for s in json.loads(row.get('steps', '[]'))]
                    flows.append(ApprovalFlow(
                        id=row['id'],
                        name=row['name'],
                        description=row.get('description', ''),
                        approval_type=ApprovalType(row.get('approval_type', 'custom')),
                        steps=steps,
                        allow_skip=bool(row.get('allow_skip', 0)),
                        allow_revoke=bool(row.get('allow_revoke', 1)),
                        allow_delegate=bool(row.get('allow_delegate', 0)),
                        auto_expire_hours=row.get('auto_expire_hours', 168),
                        notify_on_status_change=bool(row.get('notify_on_status_change', 1)),
                        notify_on_timeout=bool(row.get('notify_on_timeout', 1)),
                        created_by=row.get('created_by'),
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    ).to_dict())
                else:
                    steps = [ApprovalStep(**s) for s in json.loads(row[4] if row[4] else '[]')]
                    flows.append(ApprovalFlow(
                        id=row[0],
                        name=row[1],
                        description=row[2] if row[2] else '',
                        approval_type=ApprovalType(row[3] if row[3] else 'custom'),
                        steps=steps,
                        allow_skip=bool(row[5] if row[5] else 0),
                        allow_revoke=bool(row[6] if row[6] else 1),
                        allow_delegate=bool(row[7] if row[7] else 0),
                        auto_expire_hours=row[8] if row[8] else 168,
                        notify_on_status_change=bool(row[9] if row[9] else 1),
                        notify_on_timeout=bool(row[10] if row[10] else 1),
                        created_by=row[11],
                        created_at=datetime.fromisoformat(row[12]),
                        updated_at=datetime.fromisoformat(row[13])
                    ).to_dict())

            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'flows': flows
            }
        except Exception as e:
            logger.error(f"列出审批流程失败: {str(e)}")
            return {'total': 0, 'page': page, 'page_size': page_size, 'flows': []}

    @synchronized(resource='approval_request_create', lock_type=LockType.WRITE)
    def create_request(self, flow_id: str, request_data: Dict) -> Optional[str]:
        """创建审批请求"""
        try:
            flow = self.get_flow(flow_id)
            if not flow:
                return None

            now = datetime.now(timezone.utc)

            # 复制流程步骤
            steps = []
            for step in flow.steps:
                new_step = ApprovalStep(
                    id=str(uuid4()),
                    step_number=step.step_number,
                    role=step.role,
                    user_id=step.user_id,
                    description=step.description,
                    required=step.required,
                    min_approvers=step.min_approvers,
                    max_approvers=step.max_approvers,
                    timeout_hours=step.timeout_hours
                )
                steps.append(new_step)

            request = ApprovalRequest(
                id=str(uuid4()),
                flow_id=flow.id,
                flow_name=flow.name,
                approval_type=flow.approval_type,
                title=request_data.get('title', ''),
                description=request_data.get('description', ''),
                data=request_data.get('data', {}),
                priority=ApprovalPriority(request_data.get('priority', 'medium')),
                requester_id=request_data.get('requester_id', ''),
                requester_name=request_data.get('requester_name', ''),
                requester_role=request_data.get('requester_role', ''),
                status=ApprovalStatus.DRAFT,
                current_step_index=0,
                steps=steps,
                created_at=now,
                updated_at=now
            )

            query = """INSERT INTO approval_requests 
                      (id, flow_id, flow_name, approval_type, title, description, data, priority,
                       requester_id, requester_name, requester_role, status, current_step_index, steps,
                       created_at, updated_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            db_manager.execute(query, (
                request.id, request.flow_id, request.flow_name, request.approval_type.value,
                request.title, request.description, json.dumps(request.data),
                request.priority.value, request.requester_id, request.requester_name,
                request.requester_role, request.status.value, request.current_step_index,
                json.dumps([s.to_dict() for s in request.steps]),
                request.created_at.isoformat(),
                request.updated_at.isoformat()
            ))

            db_sync_manager.track_change('approval_requests', request.id, ChangeType.INSERT, new_data=request.to_dict())
            logger.info(f"创建审批请求成功: {request.id}")
            return request.id
        except Exception as e:
            logger.error(f"创建审批请求失败: {str(e)}")
            return None

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """获取审批请求"""
        try:
            query = "SELECT * FROM approval_requests WHERE id = ?"
            result = db_manager.fetch_one(query, (request_id,))
            if not result:
                return None

            if isinstance(result, dict):
                steps = [ApprovalStep(**s) for s in json.loads(result.get('steps', '[]'))]
                return ApprovalRequest(
                    id=result['id'],
                    flow_id=result['flow_id'],
                    flow_name=result['flow_name'],
                    approval_type=ApprovalType(result.get('approval_type', 'custom')),
                    title=result['title'],
                    description=result.get('description', ''),
                    data=json.loads(result.get('data', '{}')),
                    priority=ApprovalPriority(result.get('priority', 'medium')),
                    requester_id=result['requester_id'],
                    requester_name=result['requester_name'],
                    requester_role=result['requester_role'],
                    status=ApprovalStatus(result.get('status', 'draft')),
                    current_step_index=result.get('current_step_index', 0),
                    steps=steps,
                    created_at=datetime.fromisoformat(result['created_at']),
                    updated_at=datetime.fromisoformat(result['updated_at']),
                    submitted_at=datetime.fromisoformat(result['submitted_at']) if result.get('submitted_at') else None,
                    completed_at=datetime.fromisoformat(result['completed_at']) if result.get('completed_at') else None,
                    expired_at=datetime.fromisoformat(result['expired_at']) if result.get('expired_at') else None,
                    revoked_at=datetime.fromisoformat(result['revoked_at']) if result.get('revoked_at') else None,
                    revoked_by=result.get('revoked_by')
                )
            else:
                steps = [ApprovalStep(**s) for s in json.loads(result[13] if result[13] else '[]')]
                return ApprovalRequest(
                    id=result[0],
                    flow_id=result[1],
                    flow_name=result[2],
                    approval_type=ApprovalType(result[3] if result[3] else 'custom'),
                    title=result[4],
                    description=result[5] if result[5] else '',
                    data=json.loads(result[6] if result[6] else '{}'),
                    priority=ApprovalPriority(result[7] if result[7] else 'medium'),
                    requester_id=result[8],
                    requester_name=result[9],
                    requester_role=result[10],
                    status=ApprovalStatus(result[11] if result[11] else 'draft'),
                    current_step_index=result[12] if result[12] else 0,
                    steps=steps,
                    created_at=datetime.fromisoformat(result[14]),
                    updated_at=datetime.fromisoformat(result[15]),
                    submitted_at=datetime.fromisoformat(result[16]) if result[16] else None,
                    completed_at=datetime.fromisoformat(result[17]) if result[17] else None,
                    expired_at=datetime.fromisoformat(result[18]) if result[18] else None,
                    revoked_at=datetime.fromisoformat(result[19]) if result[19] else None,
                    revoked_by=result[20]
                )
        except Exception as e:
            logger.error(f"获取审批请求失败: {str(e)}")
            return None

    @synchronized(resource='approval_submit', lock_type=LockType.WRITE)
    def submit_request(self, request_id: str) -> bool:
        """提交审批请求"""
        try:
            request = self.get_request(request_id)
            if not request:
                return False

            if request.status != ApprovalStatus.DRAFT:
                return False

            request.status = ApprovalStatus.PENDING
            request.submitted_at = datetime.now(timezone.utc)
            request.updated_at = datetime.now(timezone.utc)

            # 设置过期时间
            flow = self.get_flow(request.flow_id)
            if flow:
                request.expired_at = request.submitted_at + timedelta(hours=flow.auto_expire_hours)

            query = """UPDATE approval_requests SET 
                      status = ?, submitted_at = ?, updated_at = ?, expired_at = ?
                      WHERE id = ?"""

            db_manager.execute(query, (
                request.status.value,
                request.submitted_at.isoformat(),
                request.updated_at.isoformat(),
                request.expired_at.isoformat() if request.expired_at else None,
                request.id
            ))

            db_sync_manager.track_change('approval_requests', request.id, ChangeType.UPDATE, new_data=request.to_dict())

            # 创建通知
            self._create_notification(request_id, request.requester_id, 'created', 
                                      '审批请求已提交', f"您的审批请求 '{request.title}' 已提交")

            logger.info(f"提交审批请求成功: {request_id}")
            return True
        except Exception as e:
            logger.error(f"提交审批请求失败: {str(e)}")
            return False

    @synchronized(resource='approval_action', lock_type=LockType.WRITE)
    def approve_step(self, request_id: str, approver_id: str, comments: str = "") -> bool:
        """批准当前步骤"""
        try:
            request = self.get_request(request_id)
            if not request:
                return False

            if request.status not in [ApprovalStatus.PENDING, ApprovalStatus.IN_PROGRESS]:
                return False

            # 检查当前步骤
            if request.current_step_index >= len(request.steps):
                return False

            current_step = request.steps[request.current_step_index]

            # 检查审批权限
            if not self._has_approval_permission(approver_id, current_step):
                return False

            # 添加审批记录
            if approver_id not in current_step.approved_by:
                current_step.approved_by.append(approver_id)

            # 检查是否满足审批条件
            if len(current_step.approved_by) >= current_step.min_approvers:
                current_step.status = "approved"
                current_step.comments = comments
                current_step.completed_at = datetime.now(timezone.utc)

                # 进入下一步或完成
                if request.current_step_index < len(request.steps) - 1:
                    request.current_step_index += 1
                    request.status = ApprovalStatus.IN_PROGRESS
                else:
                    request.status = ApprovalStatus.APPROVED
                    request.completed_at = datetime.now(timezone.utc)

            request.updated_at = datetime.now(timezone.utc)

            # 保存更新
            self._save_request(request)

            # 创建通知
            self._create_notification(request_id, approver_id, 'approved',
                                      '审批已通过', 
                                      f"{request.title} 已由 {approver_id} 批准")

            # 通知下一个审批人
            if request.status == ApprovalStatus.IN_PROGRESS:
                next_step = request.steps[request.current_step_index]
                self._notify_next_approver(request, next_step)

            logger.info(f"审批步骤通过: {request_id}, step: {current_step.step_number}")
            return True
        except Exception as e:
            logger.error(f"批准步骤失败: {str(e)}")
            return False

    @synchronized(resource='approval_action', lock_type=LockType.WRITE)
    def reject_step(self, request_id: str, approver_id: str, comments: str = "") -> bool:
        """拒绝当前步骤"""
        try:
            request = self.get_request(request_id)
            if not request:
                return False

            if request.status not in [ApprovalStatus.PENDING, ApprovalStatus.IN_PROGRESS]:
                return False

            # 检查当前步骤
            if request.current_step_index >= len(request.steps):
                return False

            current_step = request.steps[request.current_step_index]

            # 检查审批权限
            if not self._has_approval_permission(approver_id, current_step):
                return False

            # 添加拒绝记录
            if approver_id not in current_step.rejected_by:
                current_step.rejected_by.append(approver_id)

            current_step.status = "rejected"
            current_step.comments = comments
            current_step.completed_at = datetime.now(timezone.utc)

            request.status = ApprovalStatus.REJECTED
            request.completed_at = datetime.now(timezone.utc)
            request.updated_at = datetime.now(timezone.utc)

            # 保存更新
            self._save_request(request)

            # 创建通知
            self._create_notification(request_id, approver_id, 'rejected',
                                      '审批已拒绝', 
                                      f"{request.title} 已由 {approver_id} 拒绝: {comments}")

            # 通知申请人
            self._create_notification(request_id, request.requester_id, 'rejected',
                                      '您的审批请求已被拒绝', 
                                      f"您的审批请求 '{request.title}' 已被拒绝: {comments}")

            logger.info(f"审批步骤拒绝: {request_id}, step: {current_step.step_number}")
            return True
        except Exception as e:
            logger.error(f"拒绝步骤失败: {str(e)}")
            return False

    @synchronized(resource='approval_revoke', lock_type=LockType.WRITE)
    def revoke_request(self, request_id: str, revoked_by: str) -> bool:
        """撤回审批请求"""
        try:
            request = self.get_request(request_id)
            if not request:
                return False

            # 检查是否可以撤回
            flow = self.get_flow(request.flow_id)
            if flow and not flow.allow_revoke:
                return False

            if request.status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
                return False

            request.status = ApprovalStatus.CANCELLED
            request.revoked_at = datetime.now(timezone.utc)
            request.revoked_by = revoked_by
            request.updated_at = datetime.now(timezone.utc)

            # 保存更新
            self._save_request(request)

            # 创建通知
            self._create_notification(request_id, revoked_by, 'cancelled',
                                      '审批已撤回', 
                                      f"{request.title} 已由 {revoked_by} 撤回")

            logger.info(f"撤回审批请求: {request_id}")
            return True
        except Exception as e:
            logger.error(f"撤回审批请求失败: {str(e)}")
            return False

    def _has_approval_permission(self, user_id: str, step: ApprovalStep) -> bool:
        """检查用户是否有审批权限"""
        # 检查指定审批人
        if step.user_id and step.user_id == user_id:
            return True

        # 检查委托关系
        if self._is_delegate(user_id, step.user_id):
            return True

        return True

    def _is_delegate(self, delegatee_id: str, delegator_id: str) -> bool:
        """检查是否有委托关系"""
        try:
            now = datetime.now(timezone.utc).isoformat()
            query = """SELECT COUNT(*) FROM approval_delegates 
                      WHERE delegator_id = ? AND delegatee_id = ? 
                      AND active = 1 AND start_time <= ? AND end_time >= ?"""
            count = db_manager.fetch_scalar(query, (delegator_id, delegatee_id, now, now)) or 0
            return count > 0
        except Exception:
            return False

    def _save_request(self, request: ApprovalRequest):
        """保存审批请求"""
        query = """UPDATE approval_requests SET 
                  status = ?, current_step_index = ?, steps = ?, 
                  updated_at = ?, completed_at = ?
                  WHERE id = ?"""

        db_manager.execute(query, (
            request.status.value,
            request.current_step_index,
            json.dumps([s.to_dict() for s in request.steps]),
            request.updated_at.isoformat(),
            request.completed_at.isoformat() if request.completed_at else None,
            request.id
        ))

        db_sync_manager.track_change('approval_requests', request.id, ChangeType.UPDATE, new_data=request.to_dict())

    def _create_notification(self, request_id: str, user_id: str, notification_type: str, 
                            title: str, message: str):
        """创建通知"""
        try:
            notification = ApprovalNotification(
                id=str(uuid4()),
                request_id=request_id,
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                created_at=datetime.now(timezone.utc)
            )

            query = """INSERT INTO approval_notifications 
                      (id, request_id, user_id, type, title, message, created_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?)"""

            db_manager.execute(query, (
                notification.id,
                notification.request_id,
                notification.user_id,
                notification.type,
                notification.title,
                notification.message,
                notification.created_at.isoformat()
            ))
        except Exception as e:
            logger.error(f"创建通知失败: {str(e)}")

    def _notify_next_approver(self, request: ApprovalRequest, step: ApprovalStep):
        """通知下一个审批人"""
        try:
            message = f"您有新的审批任务: {request.title}"
            if step.user_id:
                self._create_notification(request.id, step.user_id, 'assigned',
                                          '新的审批任务', message)
        except Exception as e:
            logger.error(f"通知审批人失败: {str(e)}")

    def list_requests(self, filters: Optional[Dict] = None, page: int = 1, page_size: int = 20) -> Dict:
        """列出审批请求"""
        try:
            conditions = []
            params = []

            if filters:
                if 'status' in filters:
                    conditions.append("status = ?")
                    params.append(filters['status'])
                if 'flow_id' in filters:
                    conditions.append("flow_id = ?")
                    params.append(filters['flow_id'])
                if 'requester_id' in filters:
                    conditions.append("requester_id = ?")
                    params.append(filters['requester_id'])
                if 'approval_type' in filters:
                    conditions.append("approval_type = ?")
                    params.append(filters['approval_type'])
                if 'priority' in filters:
                    conditions.append("priority = ?")
                    params.append(filters['priority'])

            where_str = " AND ".join(conditions) if conditions else "1=1"

            count_query = f"SELECT COUNT(*) FROM approval_requests WHERE {where_str}"
            total = db_manager.fetch_scalar(count_query, tuple(params)) or 0

            offset = (page - 1) * page_size
            query = f"SELECT * FROM approval_requests WHERE {where_str} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            rows = db_manager.fetch_all(query, tuple(params))
            requests = []

            for row in rows:
                if isinstance(row, dict):
                    steps = [ApprovalStep(**s) for s in json.loads(row.get('steps', '[]'))]
                    requests.append(ApprovalRequest(
                        id=row['id'],
                        flow_id=row['flow_id'],
                        flow_name=row['flow_name'],
                        approval_type=ApprovalType(row.get('approval_type', 'custom')),
                        title=row['title'],
                        description=row.get('description', ''),
                        data=json.loads(row.get('data', '{}')),
                        priority=ApprovalPriority(row.get('priority', 'medium')),
                        requester_id=row['requester_id'],
                        requester_name=row['requester_name'],
                        requester_role=row['requester_role'],
                        status=ApprovalStatus(row.get('status', 'draft')),
                        current_step_index=row.get('current_step_index', 0),
                        steps=steps,
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        submitted_at=datetime.fromisoformat(row['submitted_at']) if row.get('submitted_at') else None,
                        completed_at=datetime.fromisoformat(row['completed_at']) if row.get('completed_at') else None,
                        expired_at=datetime.fromisoformat(row['expired_at']) if row.get('expired_at') else None,
                        revoked_at=datetime.fromisoformat(row['revoked_at']) if row.get('revoked_at') else None,
                        revoked_by=row.get('revoked_by')
                    ).to_dict())
                else:
                    steps = [ApprovalStep(**s) for s in json.loads(row[13] if row[13] else '[]')]
                    requests.append(ApprovalRequest(
                        id=row[0],
                        flow_id=row[1],
                        flow_name=row[2],
                        approval_type=ApprovalType(row[3] if row[3] else 'custom'),
                        title=row[4],
                        description=row[5] if row[5] else '',
                        data=json.loads(row[6] if row[6] else '{}'),
                        priority=ApprovalPriority(row[7] if row[7] else 'medium'),
                        requester_id=row[8],
                        requester_name=row[9],
                        requester_role=row[10],
                        status=ApprovalStatus(row[11] if row[11] else 'draft'),
                        current_step_index=row[12] if row[12] else 0,
                        steps=steps,
                        created_at=datetime.fromisoformat(row[14]),
                        updated_at=datetime.fromisoformat(row[15]),
                        submitted_at=datetime.fromisoformat(row[16]) if row[16] else None,
                        completed_at=datetime.fromisoformat(row[17]) if row[17] else None,
                        expired_at=datetime.fromisoformat(row[18]) if row[18] else None,
                        revoked_at=datetime.fromisoformat(row[19]) if row[19] else None,
                        revoked_by=row[20]
                    ).to_dict())

            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'requests': requests
            }
        except Exception as e:
            logger.error(f"列出审批请求失败: {str(e)}")
            return {'total': 0, 'page': page, 'page_size': page_size, 'requests': []}

    @synchronized(resource='approval_delegate', lock_type=LockType.WRITE)
    def create_delegate(self, delegator_id: str, delegatee_id: str, 
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       approval_types: Optional[List[str]] = None) -> Optional[str]:
        """创建审批委托"""
        try:
            now = datetime.now(timezone.utc)
            delegate = ApprovalDelegate(
                id=str(uuid4()),
                delegator_id=delegator_id,
                delegatee_id=delegatee_id,
                start_time=start_time or now,
                end_time=end_time or (now + timedelta(days=7)),
                approval_types=approval_types or [],
                created_at=now
            )

            query = """INSERT INTO approval_delegates 
                      (id, delegator_id, delegatee_id, start_time, end_time, approval_types, created_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?)"""

            db_manager.execute(query, (
                delegate.id,
                delegate.delegator_id,
                delegate.delegatee_id,
                delegate.start_time.isoformat(),
                delegate.end_time.isoformat(),
                json.dumps(delegate.approval_types),
                delegate.created_at.isoformat()
            ))

            db_sync_manager.track_change('approval_delegates', delegate.id, ChangeType.INSERT, new_data=delegate.to_dict())
            logger.info(f"创建审批委托成功: {delegate.id}")
            return delegate.id
        except Exception as e:
            logger.error(f"创建审批委托失败: {str(e)}")
            return None

    def get_notifications(self, user_id: str, read: Optional[bool] = None, 
                         page: int = 1, page_size: int = 20) -> Dict:
        """获取用户通知"""
        try:
            conditions = ["user_id = ?"]
            params = [user_id]

            if read is not None:
                conditions.append("read = ?")
                params.append(1 if read else 0)

            where_str = " AND ".join(conditions)

            count_query = f"SELECT COUNT(*) FROM approval_notifications WHERE {where_str}"
            total = db_manager.fetch_scalar(count_query, tuple(params)) or 0

            offset = (page - 1) * page_size
            query = f"SELECT * FROM approval_notifications WHERE {where_str} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            rows = db_manager.fetch_all(query, tuple(params))
            notifications = []

            for row in rows:
                if isinstance(row, dict):
                    notifications.append(ApprovalNotification(
                        id=row['id'],
                        request_id=row['request_id'],
                        user_id=row['user_id'],
                        type=row['type'],
                        title=row['title'],
                        message=row['message'],
                        read=bool(row.get('read', 0)),
                        created_at=datetime.fromisoformat(row['created_at']),
                        read_at=datetime.fromisoformat(row['read_at']) if row.get('read_at') else None
                    ).to_dict())
                else:
                    notifications.append(ApprovalNotification(
                        id=row[0],
                        request_id=row[1],
                        user_id=row[2],
                        type=row[3],
                        title=row[4],
                        message=row[5],
                        read=bool(row[6] if row[6] else 0),
                        created_at=datetime.fromisoformat(row[7]),
                        read_at=datetime.fromisoformat(row[8]) if row[8] else None
                    ).to_dict())

            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'notifications': notifications
            }
        except Exception as e:
            logger.error(f"获取通知失败: {str(e)}")
            return {'total': 0, 'page': page, 'page_size': page_size, 'notifications': []}

    @synchronized(resource='notification_read', lock_type=LockType.WRITE)
    def mark_notification_read(self, notification_id: str) -> bool:
        """标记通知为已读"""
        try:
            query = """UPDATE approval_notifications SET 
                      read = 1, read_at = ?
                      WHERE id = ?"""

            db_manager.execute(query, (datetime.now(timezone.utc).isoformat(), notification_id))
            return True
        except Exception as e:
            logger.error(f"标记通知已读失败: {str(e)}")
            return False

    def get_stats(self) -> ApprovalStats:
        """获取审批统计"""
        try:
            # 获取总数和各状态数量
            query = """SELECT 
                      COUNT(*),
                      SUM(CASE WHEN status = 'pending' OR status = 'in_progress' THEN 1 ELSE 0 END),
                      SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END),
                      SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END),
                      SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END)
                      FROM approval_requests"""
            result = db_manager.fetch_one(query)

            if result:
                if isinstance(result, dict):
                    total = result[0] if result[0] else 0
                    pending = result[1] if result[1] else 0
                    approved = result[2] if result[2] else 0
                    rejected = result[3] if result[3] else 0
                    cancelled = result[4] if result[4] else 0
                else:
                    total = result[0] if result[0] else 0
                    pending = result[1] if result[1] else 0
                    approved = result[2] if result[2] else 0
                    rejected = result[3] if result[3] else 0
                    cancelled = result[4] if result[4] else 0
            else:
                total = pending = approved = rejected = cancelled = 0

            # 计算平均处理时间
            query = """SELECT AVG(strftime('%s', completed_at) - strftime('%s', submitted_at)) / 3600 
                      FROM approval_requests 
                      WHERE status = 'approved' AND submitted_at IS NOT NULL AND completed_at IS NOT NULL"""
            avg_hours = db_manager.fetch_scalar(query) or 0.0

            # 计算通过率
            approval_rate = approved / (approved + rejected) if (approved + rejected) > 0 else 0.0

            # 获取按类型统计的待处理数量
            query = """SELECT approval_type, COUNT(*) FROM approval_requests 
                      WHERE status = 'pending' OR status = 'in_progress' 
                      GROUP BY approval_type"""
            type_counts = db_manager.fetch_all(query)
            pending_by_type = {}
            for row in type_counts:
                if isinstance(row, dict):
                    pending_by_type[row['approval_type']] = row['COUNT(*)']
                else:
                    pending_by_type[row[0]] = row[1]

            # 获取按优先级统计的待处理数量
            query = """SELECT priority, COUNT(*) FROM approval_requests 
                      WHERE status = 'pending' OR status = 'in_progress' 
                      GROUP BY priority"""
            priority_counts = db_manager.fetch_all(query)
            pending_by_priority = {}
            for row in priority_counts:
                if isinstance(row, dict):
                    pending_by_priority[row['priority']] = row['COUNT(*)']
                else:
                    pending_by_priority[row[0]] = row[1]

            return ApprovalStats(
                total_requests=total,
                pending_requests=pending,
                approved_requests=approved,
                rejected_requests=rejected,
                cancelled_requests=cancelled,
                avg_processing_time_hours=avg_hours,
                approval_rate=approval_rate,
                pending_by_type=pending_by_type,
                pending_by_priority=pending_by_priority
            )
        except Exception as e:
            logger.error(f"获取统计失败: {str(e)}")
            return ApprovalStats()


# 创建全局实例
approval_service = ApprovalService()
