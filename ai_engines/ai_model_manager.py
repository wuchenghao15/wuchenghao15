#!/usr/bin/env python3
"""AI模型管理Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIModelManager(AIEmployee):
    """AI模型管理Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI模型管理专家"):
        super().__init__(employee_id, name, 'model_manager', 8)
        self.skills = [
            '模型注册', '模型加载', '模型卸载',
            '模型训练', '模型评估', '模型部署',
            '模型版本', '模型监控', '模型优化'
        ]
        self.models = {}
        self.model_history = []
        self.total_models = 0
    
    def register_model(self, model_info: Dict) -> Dict[str, Any]:
        """注册模型"""
        model_id = model_info.get('model_id', f"model_{datetime.now().timestamp()}")
        
        model = {
            'model_id': model_id,
            'name': model_info.get('name', ''),
            'type': model_info.get('type', ''),
            'version': model_info.get('version', '1.0.0'),
            'description': model_info.get('description', ''),
            'framework': model_info.get('framework', ''),
            'status': 'registered',
            'registered_at': datetime.now().isoformat(),
            'last_used_at': None,
            'usage_count': 0,
            'performance': {}
        }
        
        self.models[model_id] = model
        self.total_models += 1
        
        self.model_history.append({
            'action': 'registered',
            'model_id': model_id,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"模型注册: {model_id} - {model['name']}")
        
        return model
    
    def load_model(self, model_id: str) -> Dict[str, Any]:
        """加载模型"""
        if model_id not in self.models:
            return {'error': f"模型不存在: {model_id}"}
        
        model = self.models[model_id]
        model['status'] = 'loaded'
        model['last_used_at'] = datetime.now().isoformat()
        
        self.model_history.append({
            'action': 'loaded',
            'model_id': model_id,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"模型加载: {model_id}")
        
        return model
    
    def unload_model(self, model_id: str) -> Dict[str, Any]:
        """卸载模型"""
        if model_id not in self.models:
            return {'error': f"模型不存在: {model_id}"}
        
        model = self.models[model_id]
        model['status'] = 'unloaded'
        
        self.model_history.append({
            'action': 'unloaded',
            'model_id': model_id,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"模型卸载: {model_id}")
        
        return model
    
    def get_model(self, model_id: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_id not in self.models:
            return {'error': f"模型不存在: {model_id}"}
        
        model = self.models[model_id]
        model['usage_count'] += 1
        model['last_used_at'] = datetime.now().isoformat()
        
        return model
    
    def list_models(self) -> List[Dict]:
        """列出所有模型"""
        return list(self.models.values())
    
    def update_model(self, model_id: str, updates: Dict) -> Dict[str, Any]:
        """更新模型"""
        if model_id not in self.models:
            return {'error': f"模型不存在: {model_id}"}
        
        model = self.models[model_id]
        
        for key, value in updates.items():
            if key in model:
                model[key] = value
        
        model['updated_at'] = datetime.now().isoformat()
        
        self.model_history.append({
            'action': 'updated',
            'model_id': model_id,
            'updates': list(updates.keys()),
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"模型更新: {model_id}")
        
        return model
    
    def delete_model(self, model_id: str) -> bool:
        """删除模型"""
        if model_id not in self.models:
            return False
        
        del self.models[model_id]
        
        self.model_history.append({
            'action': 'deleted',
            'model_id': model_id,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"模型删除: {model_id}")
        
        return True
    
    def evaluate_model(self, model_id: str, metrics: Dict) -> Dict[str, Any]:
        """评估模型"""
        if model_id not in self.models:
            return {'error': f"模型不存在: {model_id}"}
        
        model = self.models[model_id]
        model['performance'] = metrics
        model['last_evaluated_at'] = datetime.now().isoformat()
        
        self.model_history.append({
            'action': 'evaluated',
            'model_id': model_id,
            'metrics': list(metrics.keys()),
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'model_id': model_id,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_model_stats(self) -> Dict:
        """获取模型统计"""
        loaded_count = sum(1 for m in self.models.values() if m['status'] == 'loaded')
        unloaded_count = sum(1 for m in self.models.values() if m['status'] == 'unloaded')
        
        return {
            'total_models': self.total_models,
            'loaded_models': loaded_count,
            'unloaded_models': unloaded_count,
            'model_types': self._get_model_types(),
            'recent_actions': self.model_history[-10:]
        }
    
    def _get_model_types(self) -> Dict:
        """获取模型类型统计"""
        types = {}
        for model in self.models.values():
            model_type = model.get('type', 'unknown')
            types[model_type] = types.get(model_type, 0) + 1
        
        return types

model_manager = AIModelManager('ai_model_manager_001')
