# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试数据访问对象
"""

from typing import Dict, Optional, Any

from app.data.dao.base_dao import BaseDAO


class ExamDAO(BaseDAO):
    """考试数据访问对象"""
    
    _table_name = 'exams'
    _primary_key = 'id'
    
    @classmethod
    def list_active_exams(cls, page: int = 1, page_size: int = 20) -> Dict:
        """列出活跃考试"""
        return cls.list({'status': 'active'}, page, page_size)
    
    @classmethod
    def list_by_language(cls, language: str, page: int = 1, page_size: int = 20) -> Dict:
        """按语言列出考试"""
        return cls.list({'language': language}, page, page_size)
    
    @classmethod
    def list_by_level(cls, level: str, page: int = 1, page_size: int = 20) -> Dict:
        """按难度级别列出考试"""
        return cls.list({'level': level}, page, page_size)


class QuestionDAO(BaseDAO):
    """题目数据访问对象"""
    
    _table_name = 'questions'
    _primary_key = 'id'
    
    @classmethod
    def list_by_exam(cls, exam_id: str, page: int = 1, page_size: int = 50) -> Dict:
        """列出考试的题目"""
        return cls.list({'exam_id': exam_id}, page, page_size)
    
    @classmethod
    def list_by_type(cls, question_type: str, page: int = 1, page_size: int = 50) -> Dict:
        """按类型列出题目"""
        return cls.list({'type': question_type}, page, page_size)
    
    @classmethod
    def list_by_difficulty(cls, difficulty: int, page: int = 1, page_size: int = 50) -> Dict:
        """按难度列出题目"""
        return cls.list({'difficulty': difficulty}, page, page_size)


class ExamPaperDAO(BaseDAO):
    """试卷数据访问对象"""
    
    _table_name = 'exam_papers'
    _primary_key = 'id'
    
    @classmethod
    def list_by_exam(cls, exam_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出考试的试卷"""
        return cls.list({'exam_id': exam_id}, page, page_size)
    
    @classmethod
    def list_by_user(cls, user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出用户的试卷"""
        return cls.list({'user_id': user_id}, page, page_size)
    
    @classmethod
    def list_by_status(cls, status: str, page: int = 1, page_size: int = 20) -> Dict:
        """按状态列出试卷"""
        return cls.list({'status': status}, page, page_size)


class ExamResultDAO(BaseDAO):
    """考试结果数据访问对象"""
    
    _table_name = 'exam_results'
    _primary_key = 'id'
    
    @classmethod
    def list_by_exam(cls, exam_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出考试的结果"""
        return cls.list({'exam_id': exam_id}, page, page_size)
    
    @classmethod
    def list_by_user(cls, user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """列出用户的考试结果"""
        return cls.list({'user_id': user_id}, page, page_size)
