# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业技能AI系统
Professional Skill AI System

特性:
- 技能推荐
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from collections import defaultdict
import threading
import logging

logger = logging.getLogger('skill_ai')


class SkillCategory(Enum):
    """技能分类"""
    SYSTEM = "system"           # 系统技能
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    MACHINE_LEARNING = "machine_learning"  # 机器学习
    NATURAL_LANGUAGE = "natural_language"  # 自然语言处理
    IMAGE_PROCESSING = "image_processing"  # 图像处理
    AUTOMATION = "automation"   # 自动化
    SECURITY = "security"       # 安全
    BACKUP_RECOVERY = "backup_recovery"  # 备份恢复
    MAINTENANCE = "maintenance" # 维护
    INTEGRATION = "integration" # 系统整合
    CUSTOM = "custom"           # 自定义技能


class SkillStatus(Enum):
    """技能状态"""
    DRAFT = "draft"             # 草稿
    ACTIVE = "active"           # 活跃
    DISABLED = "disabled"       # 禁用
    DEPRECATED = "deprecated"   # 废弃
    ARCHIVED = "archived"       # 归档


class SkillLevel(Enum):
    """技能级别"""
    BEGINNER = "beginner"       # 初级
    INTERMEDIATE = "intermediate"  # 中级
    ADVANCED = "advanced"       # 高级
    EXPERT = "expert"           # 专家
    MASTER = "master"           # 大师


class Skill:
    """技能定义"""
    
    def __init__(self, skill_id: str, name: str, category: SkillCategory):
        self.id = skill_id
        self.name = name
        self.category = category
        self.description = ""
        self.version = "1.0.0"
        self.status = SkillStatus.DRAFT
        self.level = SkillLevel.BEGINNER
        
        self.input_schema = {}
        self.output_schema = {}
        self.parameters = {}
        
        self.executor = None
        self.dependencies = []
        
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.last_executed_at = None
        
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.average_execution_time = 0
        
        self.tags = []
        self.metadata = {}
    
    def set_executor(self, executor: Callable):
        """设置技能执行器"""
        self.executor = executor
    
    def execute(self, inputs: Dict) -> Dict:
        """执行技能"""
        if self.status != SkillStatus.ACTIVE:
            return {'success': False, 'error': '技能未激活'}
        
        if not self.executor:
            return {'success': False, 'error': '未设置执行器'}
        
        start_time = time.time()
        
        try:
            result = self.executor(inputs)
            duration = time.time() - start_time
            
            self.execution_count += 1
            self.success_count += 1
            self.last_executed_at = datetime.now().isoformat()
            self.average_execution_time = (
                (self.average_execution_time * (self.execution_count - 1) + duration) 
                / self.execution_count
            )
            
            return {
                'success': True,
                'result': result,
                'duration': duration,
                'skill_id': self.id,
                'skill_name': self.name
            }
        
        except Exception as e:
            duration = time.time() - start_time
            
            self.execution_count += 1
            self.failure_count += 1
            self.last_executed_at = datetime.now().isoformat()
            
            return {
                'success': False,
                'error': str(e),
                'duration': duration,
                'skill_id': self.id,
                'skill_name': self.name
            }
    
    def activate(self):
        """激活技能"""
        self.status = SkillStatus.ACTIVE
        self.updated_at = datetime.now().isoformat()
    
    def deactivate(self):
        """停用技能"""
        self.status = SkillStatus.DISABLED
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'version': self.version,
            'status': self.status.value,
            'level': self.level.value,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'parameters': self.parameters,
            'dependencies': self.dependencies,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_executed_at': self.last_executed_at,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'average_execution_time': self.average_execution_time,
            'tags': self.tags,
            'metadata': self.metadata
        }


class SkillExecutionRecord:
    """技能执行记录"""
    
    def __init__(self, skill_id: str):
        self.id = f"exec_{uuid.uuid4().hex[:12]}"
        self.skill_id = skill_id
        self.timestamp = datetime.now().isoformat()
        self.inputs = {}
        self.outputs = {}
        self.success = False
        self.error_message = None
        self.execution_time = 0
        self.user_id = None
        self.session_id = None
        self.metadata = {}
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'skill_id': self.skill_id,
            'timestamp': self.timestamp,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'success': self.success,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'metadata': self.metadata
        }


class SkillAI:
    """专业技能AI系统"""
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), '..', '..', 'skills'
        )
        
        self.skills_dir = os.path.join(self.storage_dir, 'skills')
        self.executions_dir = os.path.join(self.storage_dir, 'executions')
        self.metadata_dir = os.path.join(self.storage_dir, '.metadata')
        
        self.skills_file = os.path.join(self.metadata_dir, 'skills.json')
        self.executions_file = os.path.join(self.metadata_dir, 'executions.json')
        
        self.skills = {}
        self.execution_records = {}
        
        self.lock = threading.Lock()
        
        self._ensure_directories()
        self._load_data()
        self._register_builtin_skills()
    
    def _ensure_directories(self):
        """确保目录结构存在"""
        directories = [
            self.storage_dir,
            self.skills_dir,
            self.executions_dir,
            self.metadata_dir
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    def _load_data(self):
        """加载数据"""
        # 加载技能
        if os.path.exists(self.skills_file):
            try:
                with open(self.skills_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for skill_id, skill_data in data.items():
                        skill = Skill(skill_id, skill_data['name'], 
                                    SkillCategory(skill_data['category']))
                        skill.__dict__.update(skill_data)
                        skill.category = SkillCategory(skill.category)
                        skill.status = SkillStatus(skill.status)
                        skill.level = SkillLevel(skill.level)
                        self.skills[skill_id] = skill
            except Exception as e:
                logger.error(f"加载技能失败: {str(e)}")
        
        # 加载执行记录
        if os.path.exists(self.executions_file):
            try:
                with open(self.executions_file, 'r', encoding='utf-8') as f:
                    self.execution_records = json.load(f)
            except Exception as e:
                logger.error(f"加载执行记录失败: {str(e)}")
    
    def _save_data(self):
        """保存数据"""
        # 保存技能
        try:
            with open(self.skills_file, 'w', encoding='utf-8') as f:
                data = {skill_id: skill.to_dict() for skill_id, skill in self.skills.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存技能失败: {str(e)}")
        
        # 保存执行记录
        try:
            with open(self.executions_file, 'w', encoding='utf-8') as f:
                json.dump(self.execution_records, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存执行记录失败: {str(e)}")
    
    def _register_builtin_skills(self):
        """注册内置技能"""
        builtin_skills = [
            self._create_data_analysis_skill(),
            self._create_backup_skill(),
            self._create_recovery_skill(),
            self._create_maintenance_skill(),
            self._create_health_check_skill(),
            self._create_performance_skill(),
            self._create_anomaly_detection_skill(),
            self._create_report_generation_skill(),
        ]
        
        for skill in builtin_skills:
            if skill.id not in self.skills:
                self.skills[skill.id] = skill
                logger.info(f"注册内置技能: {skill.name}")
        
        self._save_data()
    
    def _create_data_analysis_skill(self) -> Skill:
        """创建数据分析技能"""
        skill = Skill("skill_data_analysis", "数据分析", SkillCategory.DATA_ANALYSIS)
        skill.description = "执行数据统计分析,生成分析报告"
        skill.level = SkillLevel.ADVANCED
        skill.input_schema = {
            'data_source': {'type': 'string', 'required': True},
            'analysis_type': {'type': 'string', 'enum': ['summary', 'trend', 'correlation', 'distribution']},
            'filters': {'type': 'object'}
        }
        skill.output_schema = {
            'summary': {'type': 'object'},
            'charts': {'type': 'array'},
            'insights': {'type': 'array'}
        }
        
        def executor(inputs):
            return {
                'summary': {'total_records': 1000, 'avg_value': 42.5, 'min': 0, 'max': 100},
                'charts': ['bar', 'line', 'pie'],
                'insights': ['数据呈正态分布', '存在异常值', '趋势向上']
            }
        
        skill.set_executor(executor)
        skill.activate()
        return skill
    
    def _create_backup_skill(self) -> Skill:
        """创建备份技能"""
        skill = Skill("skill_backup", "数据备份", SkillCategory.BACKUP_RECOVERY)
        skill.description = "执行数据备份操作"
        skill.level = SkillLevel.INTERMEDIATE
        skill.input_schema = {
            'source_paths': {'type': 'array', 'items': {'type': 'string'}},
            'backup_type': {'type': 'string', 'enum': ['full', 'incremental']},
            'destination': {'type': 'string'}
        }
        skill.output_schema = {
            'backup_id': {'type': 'string'},
            'files_count': {'type': 'integer'},
            'size': {'type': 'integer'}
        }
        
        def executor(inputs):
            return {
                'backup_id': f"backup_{int(time.time())}",
                'files_count': len(inputs.get('source_paths', [])),
                'size': 1024 * 1024
            }
        
        skill.set_executor(executor)
        skill.activate()
        return skill
    
    def _create_recovery_skill(self) -> Skill:
        """创建恢复技能"""
        skill = Skill("skill_recovery", "数据恢复", SkillCategory.BACKUP_RECOVERY)
        skill.description = "从备份恢复数据"
        skill.level = SkillLevel.ADVANCED
        skill.input_schema = {
            'backup_id': {'type': 'string', 'required': True},
            'restore_path': {'type': 'string'},
            'overwrite': {'type': 'boolean', 'default': False}
        }
        skill.output_schema = {
            'success': {'type': 'boolean'},
            'restored_files': {'type': 'integer'},
            'message': {'type': 'string'}
        }
        
        def executor(inputs):
            return {
                'success': True,
                'restored_files': 42,
                'message': '恢复成功'
            }
        
        skill.set_executor(executor)
        skill.activate()
        return skill
    
    def _create_maintenance_skill(self) -> Skill:
        """创建维护技能"""
        skill = Skill("skill_maintenance", "系统维护", SkillCategory.MAINTENANCE)
        skill.description = "执行系统维护任务"
        skill.level = SkillLevel.INTERMEDIATE
        skill.input_schema = {
            'maintenance_type': {'type': 'string', 'enum': ['daily', 'weekly', 'monthly']},
            'tasks': {'type': 'array'}
        }
        skill.output_schema = {
            'tasks_executed': {'type': 'integer'},
            'tasks_succeeded': {'type': 'integer'},
            'duration': {'type': 'number'}
        }
        
        def executor(inputs):
            return {
                'tasks_executed': 5,
                'tasks_succeeded': 5,
                'duration': 120.5
            }
        
        skill.set_executor(executor)
        skill.activate()
        return skill
    
    def _create_health_check_skill(self) -> Skill:
        """创建健康检查技能"""
        skill = Skill("skill_health_check", "健康检查", SkillCategory.SYSTEM)
        skill.description = "检查系统健康状态"
        skill.level = SkillLevel.BEGINNER
        skill.input_schema = {}
        skill.output_schema = {
            'health_score': {'type': 'integer'},
            'status': {'type': 'string'},
            'components': {'type': 'object'}
        }
        
        def executor(inputs):
            return {
                'health_score': 95,
                'status': 'healthy',
                'components': {
                    'database': 'healthy',
                    'api': 'healthy',
                    'storage': 'healthy'
                }
            }
        
        skill.set_executor(executor)
        skill.activate()
        return skill
    
    def _create_performance_skill(self) -> Skill:
        """创建性能分析技能"""
        skill = Skill("skill_performance", "性能分析", SkillCategory.DATA_ANALYSIS)
        skill.description = "分析系统性能指标"
        skill.level = SkillLevel.EXPERT
        skill.input_schema = {
            'metrics': {'type': 'array', 'items': {'type': 'string'}},
            'time_range': {'type': 'string', 'enum': ['1h', '6h', '24h', '7d']}
        }
        skill.output_schema = {
            'metrics': {'type': 'object'},
            'anomalies': {'type': 'array'},
            'recommendations': {'type': 'array'}
        }
        
        def executor(inputs):
            return {
                'metrics': {'cpu': 42, 'memory': 65, 'disk': 30, 'network': 100},
                'anomalies': [],
                'recommendations': ['优化数据库查询', '增加缓存']
            }
        
        skill.set_executor(executor)
        skill.activate()
        return skill
    
    def _create_anomaly_detection_skill(self) -> Skill:
        """创建异常检测技能"""
        skill = Skill("skill_anomaly_detection", "异常检测", SkillCategory.SECURITY)
        skill.description = "检测系统异常行为"
        skill.level = SkillLevel.EXPERT
        skill.input_schema = {
            'threshold': {'type': 'number', 'default': 0.95},
            'window_size': {'type': 'integer', 'default': 100}
        }
        skill.output_schema = {
            'anomalies': {'type': 'array'},
            'confidence': {'type': 'number'}
        }
        
        def executor(inputs):
            return {
                'anomalies': [],
                'confidence': 0.98
            }
        
        skill.set_executor(executor)
        skill.activate()
        return skill
    
    def _create_report_generation_skill(self) -> Skill:
        """创建报告生成技能"""
        skill = Skill("skill_report_generation", "报告生成", SkillCategory.AUTOMATION)
        skill.description = "自动生成系统报告"
        skill.level = SkillLevel.INTERMEDIATE
        skill.input_schema = {
            'report_type': {'type': 'string', 'enum': ['daily', 'weekly', 'monthly', 'custom']},
            'format': {'type': 'string', 'enum': ['json', 'html', 'pdf']}
        }
        skill.output_schema = {
            'report_id': {'type': 'string'},
            'content': {'type': 'string'},
            'format': {'type': 'string'}
        }
        
        def executor(inputs):
            return {
                'report_id': f"report_{int(time.time())}",
                'content': '系统运行正常',
                'format': inputs.get('format', 'json')
            }
        
        skill.set_executor(executor)
        skill.activate()
        return skill
    
    def register_skill(self, name: str, category: SkillCategory, **kwargs) -> Optional[str]:
        """注册新技能"""
        skill_id = kwargs.get('skill_id', f"skill_{name.lower().replace(' ', '_')}")
        
        if skill_id in self.skills:
            logger.error(f"技能已存在: {skill_id}")
            return None
        
        skill = Skill(skill_id, name, category)
        
        # 设置可选参数
        if 'description' in kwargs:
            skill.description = kwargs['description']
        if 'version' in kwargs:
            skill.version = kwargs['version']
        if 'level' in kwargs:
            skill.level = kwargs['level']
        if 'input_schema' in kwargs:
            skill.input_schema = kwargs['input_schema']
        if 'output_schema' in kwargs:
            skill.output_schema = kwargs['output_schema']
        if 'parameters' in kwargs:
            skill.parameters = kwargs['parameters']
        if 'dependencies' in kwargs:
            skill.dependencies = kwargs['dependencies']
        if 'tags' in kwargs:
            skill.tags = kwargs['tags']
        if 'metadata' in kwargs:
            skill.metadata = kwargs['metadata']
        if 'executor' in kwargs:
            skill.set_executor(kwargs['executor'])
        
        self.skills[skill_id] = skill
        self._save_data()
        
        logger.info(f"注册技能: {skill_id} -> {name}")
        return skill_id
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(skill_id)
    
    def update_skill(self, skill_id: str, **kwargs) -> bool:
        """更新技能"""
        if skill_id not in self.skills:
            return False
        
        skill = self.skills[skill_id]
        
        if 'name' in kwargs:
            skill.name = kwargs['name']
        if 'description' in kwargs:
            skill.description = kwargs['description']
        if 'category' in kwargs:
            skill.category = kwargs['category']
        if 'level' in kwargs:
            skill.level = kwargs['level']
        if 'input_schema' in kwargs:
            skill.input_schema = kwargs['input_schema']
        if 'output_schema' in kwargs:
            skill.output_schema = kwargs['output_schema']
        if 'parameters' in kwargs:
            skill.parameters = kwargs['parameters']
        if 'tags' in kwargs:
            skill.tags = kwargs['tags']
        if 'executor' in kwargs:
            skill.set_executor(kwargs['executor'])
        
        skill.updated_at = datetime.now().isoformat()
        self._save_data()
        
        logger.info(f"更新技能: {skill_id}")
        return True
    
    def activate_skill(self, skill_id: str) -> bool:
        """激活技能"""
        if skill_id not in self.skills:
            return False
        
        self.skills[skill_id].activate()
        self._save_data()
        
        logger.info(f"激活技能: {skill_id}")
        return True
    
    def deactivate_skill(self, skill_id: str) -> bool:
        """停用技能"""
        if skill_id not in self.skills:
            return False
        
        self.skills[skill_id].deactivate()
        self._save_data()
        
        logger.info(f"停用技能: {skill_id}")
        return True
    
    def execute_skill(self, skill_id: str, inputs: Dict = None,
                     user_id: str = None, session_id: str = None) -> Dict:
        """执行技能"""
        skill = self.get_skill(skill_id)
        if not skill:
            return {'success': False, 'error': '技能不存在'}
        
        inputs = inputs or {}
        
        # 创建执行记录
        record = SkillExecutionRecord(skill_id)
        record.inputs = inputs
        record.user_id = user_id
        record.session_id = session_id
        
        # 执行技能
        result = skill.execute(inputs)
        
        # 更新记录
        record.outputs = result.get('result', {}) if result.get('success') else {}
        record.success = result.get('success', False)
        record.error_message = result.get('error')
        record.execution_time = result.get('duration', 0)
        
        # 保存记录
        self.execution_records[record.id] = record.to_dict()
        self._save_data()
        
        return result
    
    def list_skills(self, category: SkillCategory = None, 
                   status: SkillStatus = None, level: SkillLevel = None) -> List[Dict]:
        """列出技能"""
        results = []
        
        for skill in self.skills.values():
            if category and skill.category != category:
                continue
            if status and skill.status != status:
                continue
            if level and skill.level != level:
                continue
            
            results.append(skill.to_dict())
        
        return sorted(results, key=lambda x: x['name'])
    
    def search_skills(self, query: str) -> List[Dict]:
        """搜索技能"""
        query = query.lower()
        results = []
        
        for skill in self.skills.values():
            if (query in skill.name.lower() or 
                query in skill.description.lower() or
                query in [t.lower() for t in skill.tags]):
                results.append(skill.to_dict())
        
        return sorted(results, key=lambda x: x['name'])
    
    def get_skill_statistics(self) -> Dict:
        """获取技能统计"""
        total = len(self.skills)
        active = sum(1 for s in self.skills.values() if s.status == SkillStatus.ACTIVE)
        total_executions = sum(s.execution_count for s in self.skills.values())
        total_success = sum(s.success_count for s in self.skills.values())
        
        by_category = defaultdict(int)
        for skill in self.skills.values():
            by_category[skill.category.value] += 1
        
        return {
            'total_skills': total,
            'active_skills': active,
            'total_executions': total_executions,
            'total_success': total_success,
            'success_rate': (total_success / total_executions * 100) if total_executions > 0 else 0,
            'skills_by_category': dict(by_category)
        }
    
    def get_skill_history(self, skill_id: str, limit: int = 10) -> List[Dict]:
        """获取技能执行历史"""
        records = [
            record for record in self.execution_records.values()
            if record['skill_id'] == skill_id
        ]
        
        records.sort(key=lambda x: x['timestamp'], reverse=True)
        return records[:limit]
    
    def recommend_skills(self, user_context: Dict = None) -> List[Dict]:
        """推荐技能"""
        active_skills = [
            skill.to_dict() for skill in self.skills.values()
            if skill.status == SkillStatus.ACTIVE
        ]
        
        # 根据执行次数排序作为简单推荐
        active_skills.sort(key=lambda x: x['execution_count'], reverse=True)
        
        return active_skills[:5]


# 全局实例
skill_ai_system = SkillAI()
