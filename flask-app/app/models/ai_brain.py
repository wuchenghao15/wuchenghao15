#!/usr/bin/env python3
"""
AI脑库数据模型
"""

import json
from datetime import datetime
from app.models.base_model import BaseModel


class AIBrainKnowledge(BaseModel):
    """AI脑库知识模型"""
    
    table_name = 'ai_brain_knowledge'
    primary_key = 'knowledge_id'
    columns = {
        'knowledge_id': 'TEXT PRIMARY KEY',
        'title': 'TEXT NOT NULL',
        'content': 'TEXT NOT NULL',
        'knowledge_type': 'TEXT NOT NULL',
        'knowledge_category': 'TEXT DEFAULT "uncategorized"',
        'source': 'TEXT NOT NULL',
        'source_id': 'TEXT',
        'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'tags': 'TEXT',
        'priority': 'INTEGER DEFAULT 0',
        'is_active': 'BOOLEAN DEFAULT TRUE',
        'review_status': 'TEXT DEFAULT "pending"',
        'reviewed_by': 'TEXT',
        'reviewed_at': 'DATETIME',
        'confidence_score': 'REAL DEFAULT 0.5',
        'version': 'INTEGER DEFAULT 1',
        'parent_id': 'TEXT',
        'quality_score': 'REAL DEFAULT 0.5',
        'accuracy_score': 'REAL DEFAULT 0.5',
        'relevance_score': 'REAL DEFAULT 0.5',
        'completeness_score': 'REAL DEFAULT 0.5',
        'last_used_at': 'DATETIME',
        'usage_count': 'INTEGER DEFAULT 0'
    }
    
    def __init__(self, **kwargs):
        """初始化AI脑库知识"""
        # 处理JSON类型字段
        if 'tags' in kwargs and isinstance(kwargs['tags'], list):
            kwargs['tags'] = json.dumps(kwargs['tags'])
        
        # 调用父类初始化方法
        super().__init__(**kwargs)
    
    def __getattr__(self, name):
        """获取属性值，处理JSON类型字段"""
        if name in self._data:
            value = self._data[name]
            # 处理JSON类型字段
            if name == 'tags' and value:
                if isinstance(value, str):
                    return json.loads(value)
            return value
        raise AttributeError(f"模型 {self.__class__.__name__} 没有属性 {name}")
    
    def __setattr__(self, name, value):
        """设置属性值，处理JSON类型字段"""
        if name in ['_data', '_dirty']:
            super().__setattr__(name, value)
        elif name in self.columns:
            # 处理JSON类型字段
            if name == 'tags':
                if isinstance(value, list):
                    value = json.dumps(value)
            
            # 更新数据并标记为脏
            if self._data.get(name) != value:
                self._data[name] = value
                self._dirty.add(name)
        else:
            super().__setattr__(name, value)
    
    def to_dict(self):
        """转换为字典"""
        result = {}
        for key, value in self._data.items():
            if key == 'tags' and value:
                if isinstance(value, str):
                    result[key] = json.loads(value)
                else:
                    result[key] = value
            else:
                result[key] = value
        return result
    
    @classmethod
    def get_all(cls, knowledge_type=None, source=None, tags=None):
        """获取所有知识"""
        # 构建过滤条件
        where_clause = "is_active = ?"
        where_params = [True]
        
        if knowledge_type:
            where_clause += " AND knowledge_type = ?"
            where_params.append(knowledge_type)
        
        if source:
            where_clause += " AND source = ?"
            where_params.append(source)
        
        # 使用BaseModel.filter获取结果
        knowledge_list = cls.filter(where_clause=where_clause, where_params=where_params)
        
        # 检查标签过滤
        if tags:
            filtered_knowledge = []
            for knowledge in knowledge_list:
                if any(tag in knowledge.tags for tag in tags):
                    filtered_knowledge.append(knowledge)
            return filtered_knowledge
        
        return knowledge_list
    
    def save(self):
        """保存到数据库，支持版本管理"""
        from uuid import uuid4
        
        # 如果是更新操作，创建新版本
        if hasattr(self, 'knowledge_id') and self.knowledge_id:
            # 获取现有记录
            existing_knowledge = AIBrainKnowledge.get_by_id(self.knowledge_id)
            if existing_knowledge:
                # 检查内容是否有变化
                if (existing_knowledge.title != self.title or 
                    existing_knowledge.content != self.content or
                    existing_knowledge.knowledge_type != self.knowledge_type):
                    
                    # 创建新版本
                    self.version = existing_knowledge.version + 1
                    self.parent_id = self.knowledge_id
                    # 生成新的知识ID
                    self.knowledge_id = f"knowledge-{uuid4().hex[:8]}"
                    
                    # 标记旧版本为非活动状态
                    existing_knowledge.is_active = False
                    existing_knowledge.updated_at = datetime.now()
                    super(AIBrainKnowledge, existing_knowledge).save()
        elif not hasattr(self, 'knowledge_id') or not self.knowledge_id:
            # 生成新的知识ID
            self.knowledge_id = f"knowledge-{uuid4().hex[:8]}"
        
        # 更新时间
        self.updated_at = datetime.now()
        
        # 调用父类的save方法
        return super().save()
    
    def auto_categorize(self):
        """自动分类知识"""
        from app.ai.ai_engine_integrator import ai_engine_integrator
        
        prompt = f"请根据以下知识内容，将其分类到最合适的类别中：\n\n标题：{self.title}\n内容：{self.content}\n\n请从以下类别中选择一个最合适的：\n1. 技术知识\n2. 业务规则\n3. 系统配置\n4. 最佳实践\n5. 故障处理\n6. 其他\n\n只返回类别名称，不要返回其他内容。"
        
        response = ai_engine_integrator.call_engine("zhipu", prompt)
        if response and response.get("code") == 0:
            category = response.get("data", {}).get("response", "uncategorized").strip()
            self.knowledge_category = category
            logger.info(f"知识自动分类成功：{self.title} -> {category}")
        
        return self
    
    def evaluate_quality(self):
        """评估知识质量"""
        from app.ai.ai_engine_integrator import ai_engine_integrator
        
        prompt = f"请评估以下知识的质量，从准确性、相关性和完整性三个维度进行评分，每个维度评分范围为0-1，保留两位小数：\n\n标题：{self.title}\n内容：{self.content}\n\n请按照以下格式返回结果：\n准确性：0.XX\n相关性：0.XX\n完整性：0.XX\n\n只返回评分，不要返回其他内容。"
        
        response = ai_engine_integrator.call_engine("zhipu", prompt)
        if response and response.get("code") == 0:
            evaluation = response.get("data", {}).get("response", "").strip()
            
            try:
                # 解析评分
                lines = evaluation.split('\n')
                for line in lines:
                    if '准确性：' in line:
                        self.accuracy_score = float(line.split('：')[1])
                    elif '相关性：' in line:
                        self.relevance_score = float(line.split('：')[1])
                    elif '完整性：' in line:
                        self.completeness_score = float(line.split('：')[1])
                
                # 计算综合质量分数
                self.quality_score = (self.accuracy_score + self.relevance_score + self.completeness_score) / 3
                logger.info(f"知识质量评估完成：{self.title} -> 质量分数：{self.quality_score:.2f}")
            except Exception as e:
                logger.error(f"解析质量评估结果失败：{str(e)}")
        
        return self
    
    def update_usage(self):
        """更新知识使用情况"""
        self.usage_count = getattr(self, 'usage_count', 0) + 1
        self.last_used_at = datetime.now()
        return self
    
    @classmethod
    def search(cls, keyword, knowledge_type=None):
        """搜索知识"""
        from app.utils.db import db_manager
        
        query = f"SELECT * FROM {cls.table_name} WHERE is_active = ? AND (title LIKE ? OR content LIKE ?)"
        params = [True, f"%{keyword}%", f"%{keyword}%"]
        
        if knowledge_type:
            query += " AND knowledge_type = ?"
            params.append(knowledge_type)
        
        rows = db_manager.fetch_all(query, params)
        return [cls(**dict(row)) for row in rows]


class AIBrainActivity(BaseModel):
    """AI脑库活动日志模型"""
    
    table_name = 'ai_brain_activity'
    primary_key = 'activity_id'
    columns = {
        'activity_id': 'TEXT PRIMARY KEY',
        'activity_type': 'TEXT NOT NULL',
        'description': 'TEXT NOT NULL',
        'source': 'TEXT NOT NULL',
        'source_id': 'TEXT',
        'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'metadata': 'TEXT'
    }
    
    def __init__(self, **kwargs):
        """初始化AI脑库活动"""
        # 处理JSON类型字段
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            kwargs['metadata'] = json.dumps(kwargs['metadata'])
        
        # 调用父类初始化方法
        super().__init__(**kwargs)
    
    def __getattr__(self, name):
        """获取属性值，处理JSON类型字段"""
        if name in self._data:
            value = self._data[name]
            # 处理JSON类型字段
            if name == 'metadata' and value:
                if isinstance(value, str):
                    return json.loads(value)
            return value
        raise AttributeError(f"模型 {self.__class__.__name__} 没有属性 {name}")
    
    def __setattr__(self, name, value):
        """设置属性值，处理JSON类型字段"""
        if name in ['_data', '_dirty']:
            super().__setattr__(name, value)
        elif name in self.columns:
            # 处理JSON类型字段
            if name == 'metadata':
                if isinstance(value, dict):
                    value = json.dumps(value)
            
            # 更新数据并标记为脏
            if self._data.get(name) != value:
                self._data[name] = value
                self._dirty.add(name)
        else:
            super().__setattr__(name, value)
    
    def to_dict(self):
        """转换为字典"""
        result = {}
        for key, value in self._data.items():
            if key == 'metadata' and value:
                if isinstance(value, str):
                    result[key] = json.loads(value)
                else:
                    result[key] = value
            else:
                result[key] = value
        return result
    
    def save(self):
        """保存到数据库"""
        # 生成活动ID
        from uuid import uuid4
        self.activity_id = f"activity-{uuid4().hex[:8]}"
        
        # 调用父类的save方法
        return super().save()
    
    @classmethod
    def get_recent(cls, limit=50):
        """获取最近的活动"""
        # 使用BaseModel.filter获取结果，按创建时间倒序
        return cls.filter(order_by="created_at DESC", limit=limit)