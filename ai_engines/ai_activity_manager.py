#!/usr/bin/env python3
"""AI智能活动管理Agent"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIActivityManager(AIEmployee):
    """AI活动管理Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI活动管理专家"):
        super().__init__(employee_id, name, 'activity_manager', 7)
        self.skills = [
            '活动策划', '活动创建', '活动推广',
            '报名管理', '活动执行', '活动评估',
            '活动数据分析', '活动预算管理', '活动复盘'
        ]
        self.activity_history = []
        self.total_activities = 0
        self.total_participants = 0
    
    def manage_activities(self, action: str, **kwargs) -> Dict[str, Any]:
        """活动管理"""
        actions = {
            'create': self._create_activity,
            'update': self._update_activity,
            'cancel': self._cancel_activity,
            'list': self._list_activities
        }
        if action in actions:
            return actions[action](**kwargs)
        return {'success': False, 'message': f'未知操作: {action}'}
    
    def _create_activity(self, **kwargs) -> Dict[str, Any]:
        activity = {
            'activity_id': kwargs.get('activity_id', f'act_{datetime.now().timestamp()}'),
            'name': kwargs.get('name', ''),
            'description': kwargs.get('description', ''),
            'type': kwargs.get('type', 'general'),
            'start_date': kwargs.get('start_date', datetime.now().isoformat()),
            'end_date': kwargs.get('end_date', ''),
            'location': kwargs.get('location', ''),
            'max_participants': kwargs.get('max_participants', 100),
            'budget': kwargs.get('budget', 0),
            'status': 'planning',
            'created_at': datetime.now().isoformat()
        }
        self.activity_history.append(activity)
        self.total_activities += 1
        return {'success': True, 'activity': activity}
    
    def _update_activity(self, **kwargs) -> Dict[str, Any]:
        activity_id = kwargs.get('activity_id')
        for activity in self.activity_history:
            if activity['activity_id'] == activity_id:
                activity.update(kwargs)
                activity['updated_at'] = datetime.now().isoformat()
                return {'success': True, 'activity': activity}
        return {'success': False, 'message': '活动不存在'}
    
    def _cancel_activity(self, **kwargs) -> Dict[str, Any]:
        activity_id = kwargs.get('activity_id')
        reason = kwargs.get('reason', '')
        for activity in self.activity_history:
            if activity['activity_id'] == activity_id:
                activity['status'] = 'cancelled'
                activity['cancel_reason'] = reason
                activity['cancelled_at'] = datetime.now().isoformat()
                return {'success': True, 'message': '活动已取消'}
        return {'success': False, 'message': '活动不存在'}
    
    def _list_activities(self, **kwargs) -> Dict[str, Any]:
        activity_type = kwargs.get('type')
        status = kwargs.get('status')
        activities = self.activity_history
        if activity_type:
            activities = [a for a in activities if a.get('type') == activity_type]
        if status:
            activities = [a for a in activities if a.get('status') == status]
        return {'success': True, 'activities': activities, 'count': len(activities)}
    
    def manage_registrations(self, action: str, **kwargs) -> Dict[str, Any]:
        """报名管理"""
        actions = {
            'register': self._register_participant,
            'cancel': self._cancel_registration,
            'list': self._list_participants
        }
        if action in actions:
            return actions[action](**kwargs)
        return {'success': False, 'message': f'未知操作: {action}'}
    
    def _register_participant(self, **kwargs) -> Dict[str, Any]:
        activity_id = kwargs.get('activity_id')
        participant = {
            'participant_id': kwargs.get('participant_id', f'part_{datetime.now().timestamp()}'),
            'activity_id': activity_id,
            'user_id': kwargs.get('user_id', ''),
            'name': kwargs.get('name', ''),
            'email': kwargs.get('email', ''),
            'registered_at': datetime.now().isoformat(),
            'status': 'confirmed'
        }
        for activity in self.activity_history:
            if activity['activity_id'] == activity_id:
                if 'participants' not in activity:
                    activity['participants'] = []
                if len(activity['participants']) < activity.get('max_participants', 100):
                    activity['participants'].append(participant)
                    self.total_participants += 1
                    return {'success': True, 'participant': participant}
                return {'success': False, 'message': '活动已满'}
        return {'success': False, 'message': '活动不存在'}
    
    def _cancel_registration(self, **kwargs) -> Dict[str, Any]:
        activity_id = kwargs.get('activity_id')
        participant_id = kwargs.get('participant_id')
        for activity in self.activity_history:
            if activity['activity_id'] == activity_id and 'participants' in activity:
                for i, part in enumerate(activity['participants']):
                    if part['participant_id'] == participant_id:
                        del activity['participants'][i]
                        self.total_participants -= 1
                        return {'success': True, 'message': '报名已取消'}
                return {'success': False, 'message': '参与者不存在'}
        return {'success': False, 'message': '活动不存在'}
    
    def _list_participants(self, **kwargs) -> Dict[str, Any]:
        activity_id = kwargs.get('activity_id')
        for activity in self.activity_history:
            if activity['activity_id'] == activity_id:
                participants = activity.get('participants', [])
                return {'success': True, 'participants': participants, 'count': len(participants)}
        return {'success': False, 'message': '活动不存在'}
    
    def analyze_activity(self, activity_id: str) -> Dict[str, Any]:
        """分析活动效果"""
        for activity in self.activity_history:
            if activity['activity_id'] == activity_id:
                participants = activity.get('participants', [])
                actual_participants = len(participants)
                max_participants = activity.get('max_participants', 100)
                budget = activity.get('budget', 0)
                participation_rate = (actual_participants / max_participants * 100) if max_participants > 0 else 0
                return {
                    'success': True,
                    'analysis': {
                        'activity_id': activity_id,
                        'activity_name': activity.get('name'),
                        'participation_rate': round(participation_rate, 2),
                        'actual_participants': actual_participants,
                        'max_participants': max_participants,
                        'budget': budget,
                        'status': activity.get('status'),
                        'revenue_per_participant': round(budget / actual_participants, 2) if actual_participants > 0 else 0
                    }
                }
        return {'success': False, 'message': '活动不存在'}
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_activities': self.total_activities,
            'total_participants': self.total_participants,
            'activity_history_count': len(self.activity_history),
            'employee_id': self.employee_id,
            'name': self.name,
            'employee_type': self.employee_type
        }