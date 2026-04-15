#!/usr/bin/env python3
"""
本地数据上传模型，用于存储本地数据上传记录
"""

from app.models.base_model import BaseModel

class LocalData(BaseModel):
    """本地数据上传记录模型"""
    
    table_name = 'local_data_uploads'
    primary_key = 'id'
    columns = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'data_type': 'TEXT NOT NULL',  # 数据类型：feature, log, config, etc.
        'file_path': 'TEXT',  # 本地文件路径
        'content': 'TEXT',  # 数据内容（JSON格式）
        'status': 'TEXT DEFAULT "pending"',  # 状态：pending, processing, completed, failed
        'processed_by': 'TEXT',  # 处理的AI员工ID
        'process_result': 'TEXT',  # 处理结果
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }
    
    def __init__(self, **kwargs):
        """初始化模型实例"""
        super().__init__(**kwargs)
    
    @classmethod
    def create_table(cls):
        """创建表"""
        result = super().create_table()
        if result:
            from app.utils.logging import logger
            logger.info(f"表 {cls.table_name} 创建成功")
        return result
    
    def process_data(self, ai_employee_id):
        """处理数据"""
        from app.utils.logging import logger
        from app.ai.user_ai_manager import user_ai_manager
        
        try:
            logger.info(f"AI员工 {ai_employee_id} 开始处理本地数据 {self._data['id']}")
            
            # 更新数据状态为处理中
            self._data['status'] = 'processing'
            self._data['processed_by'] = ai_employee_id
            self.save()
            
            # 调用AI员工处理数据
            result = user_ai_manager.assign_task_to_ai(ai_employee_id, {
                'task_type': 'process_local_data',
                'data_id': self._data['id'],
                'data_type': self._data['data_type'],
                'content': self._data['content']
            })
            
            # 更新数据状态为已完成
            self._data['status'] = 'completed'
            self._data['process_result'] = 'success' if result else 'failed'
            self.save()
            
            logger.info(f"AI员工 {ai_employee_id} 处理本地数据 {self._data['id']} 完成，结果：{self._data['process_result']}")
            return True
        except Exception as e:
            logger.error(f"AI员工 {ai_employee_id} 处理本地数据 {self._data['id']} 失败：{str(e)}")
            self._data['status'] = 'failed'
            self._data['process_result'] = str(e)
            self.save()
            return False
