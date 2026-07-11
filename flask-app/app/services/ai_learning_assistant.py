"""智能学习助手服务 - MTSCOS AI项目

提供个性化学习推荐、智能作业辅导和学习效果分析功能
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.utils.logging import logger
from app.utils.db import DatabaseManager
from app.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    BusinessException
)

db_manager = DatabaseManager()


class LearningRecommendation:
    """学习推荐模型"""
    
    TABLE_NAME = 'learning_recommendations'
    
    @classmethod
    def _create_table(cls):
        """创建推荐表"""
        try:
            db_manager.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    recommendation_type TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    confidence REAL DEFAULT 0.0,
                    priority INTEGER DEFAULT 0,
                    viewed INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db_manager.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_rec_user ON {cls.TABLE_NAME}(user_id)
            """)
        except Exception as e:
            logger.error(f"创建学习推荐表失败: {str(e)}")
    
    @classmethod
    def create(cls, user_id: int, rec_type: str, content_id: str, 
               content_type: str, title: str, description: str = '', 
               confidence: float = 0.0, priority: int = 0) -> str:
        """创建学习推荐"""
        cls._create_table()
        try:
            rec_id = f"rec_{uuid4().hex[:8]}"
            db_manager.execute(f"""
                INSERT INTO {cls.TABLE_NAME} 
                (id, user_id, recommendation_type, content_id, content_type, 
                 title, description, confidence, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rec_id, user_id, rec_type, content_id, content_type, 
                  title, description, confidence, priority, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
            return rec_id
        except Exception as e:
            logger.error(f"创建学习推荐失败: {str(e)}")
            return ''
    
    @classmethod
    def get_user_recommendations(cls, user_id: int, limit: int = 10) -> List[Dict]:
        """获取用户推荐列表"""
        cls._create_table()
        try:
            results = db_manager.fetch_all(f"""
                SELECT * FROM {cls.TABLE_NAME} 
                WHERE user_id = ? AND viewed = 0
                ORDER BY priority DESC, confidence DESC LIMIT ?
            """, (user_id, limit))
            
            recommendations = []
            for result in results:
                recommendations.append({
                    'id': result[0],
                    'user_id': result[1],
                    'recommendation_type': result[2],
                    'content_id': result[3],
                    'content_type': result[4],
                    'title': result[5],
                    'description': result[6],
                    'confidence': result[7],
                    'priority': result[8],
                    'viewed': bool(result[9]),
                    'completed': bool(result[10]),
                    'created_at': result[11],
                    'updated_at': result[12]
                })
            return recommendations
        except Exception as e:
            logger.error(f"获取用户推荐失败: {str(e)}")
            return []
    
    @classmethod
    def mark_viewed(cls, rec_id: str) -> bool:
        """标记已查看"""
        try:
            db_manager.execute(f"""
                UPDATE {cls.TABLE_NAME} SET viewed = 1, updated_at = ? WHERE id = ?
            """, (datetime.now().isoformat(), rec_id))
            return True
        except Exception as e:
            logger.error(f"标记推荐已查看失败: {str(e)}")
            return False
    
    @classmethod
    def mark_completed(cls, rec_id: str) -> bool:
        """标记已完成"""
        try:
            db_manager.execute(f"""
                UPDATE {cls.TABLE_NAME} SET completed = 1, updated_at = ? WHERE id = ?
            """, (datetime.now().isoformat(), rec_id))
            return True
        except Exception as e:
            logger.error(f"标记推荐已完成失败: {str(e)}")
            return False


class HomeworkAssistant:
    """作业辅导模型"""
    
    TABLE_NAME = 'homework_assistants'
    
    @classmethod
    def _create_table(cls):
        """创建作业辅导表"""
        try:
            db_manager.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    homework_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    question_text TEXT,
                    user_answer TEXT,
                    correct_answer TEXT,
                    analysis TEXT,
                    hints TEXT,
                    steps TEXT,
                    score INTEGER,
                    max_score INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db_manager.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_assist_user ON {cls.TABLE_NAME}(user_id)
            """)
            db_manager.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_assist_homework ON {cls.TABLE_NAME}(homework_id)
            """)
        except Exception as e:
            logger.error(f"创建作业辅导表失败: {str(e)}")
    
    @classmethod
    def create_assistance(cls, user_id: int, homework_id: str, question_id: str, 
                         question_text: str, user_answer: str = '') -> str:
        """创建作业辅导记录"""
        cls._create_table()
        try:
            assist_id = f"assist_{uuid4().hex[:8]}"
            db_manager.execute(f"""
                INSERT INTO {cls.TABLE_NAME} 
                (id, user_id, homework_id, question_id, question_text, user_answer, 
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (assist_id, user_id, homework_id, question_id, question_text, 
                  user_answer, 'pending', datetime.now().isoformat(), datetime.now().isoformat()))
            return assist_id
        except Exception as e:
            logger.error(f"创建作业辅导失败: {str(e)}")
            return ''
    
    @classmethod
    def get_assistance(cls, assist_id: str) -> Optional[Dict]:
        """获取作业辅导详情"""
        try:
            result = db_manager.fetch_one(f"""
                SELECT * FROM {cls.TABLE_NAME} WHERE id = ?
            """, (assist_id,))
            
            if result:
                return {
                    'id': result[0],
                    'user_id': result[1],
                    'homework_id': result[2],
                    'question_id': result[3],
                    'question_text': result[4],
                    'user_answer': result[5],
                    'correct_answer': result[6],
                    'analysis': result[7],
                    'hints': result[8],
                    'steps': result[9],
                    'score': result[10],
                    'max_score': result[11],
                    'status': result[12],
                    'created_at': result[13],
                    'updated_at': result[14]
                }
        except Exception as e:
            logger.error(f"获取作业辅导失败: {str(e)}")
        return None
    
    @classmethod
    def update_assistance(cls, assist_id: str, **kwargs) -> bool:
        """更新作业辅导"""
        try:
            update_fields = []
            params = []
            
            if 'user_answer' in kwargs:
                update_fields.append('user_answer = ?')
                params.append(kwargs['user_answer'])
            if 'correct_answer' in kwargs:
                update_fields.append('correct_answer = ?')
                params.append(kwargs['correct_answer'])
            if 'analysis' in kwargs:
                update_fields.append('analysis = ?')
                params.append(kwargs['analysis'])
            if 'hints' in kwargs:
                update_fields.append('hints = ?')
                params.append(kwargs['hints'])
            if 'steps' in kwargs:
                update_fields.append('steps = ?')
                params.append(kwargs['steps'])
            if 'score' in kwargs:
                update_fields.append('score = ?')
                params.append(kwargs['score'])
            if 'max_score' in kwargs:
                update_fields.append('max_score = ?')
                params.append(kwargs['max_score'])
            if 'status' in kwargs:
                update_fields.append('status = ?')
                params.append(kwargs['status'])
            
            if update_fields:
                update_fields.append('updated_at = ?')
                params.append(datetime.now().isoformat())
                params.append(assist_id)
                
                db_manager.execute(f"""
                    UPDATE {cls.TABLE_NAME} SET {', '.join(update_fields)} WHERE id = ?
                """, tuple(params))
                return True
        except Exception as e:
            logger.error(f"更新作业辅导失败: {str(e)}")
        return False
    
    @classmethod
    def get_user_homework_assistance(cls, user_id: int, homework_id: str = None) -> List[Dict]:
        """获取用户作业辅导列表"""
        try:
            if homework_id:
                results = db_manager.fetch_all(f"""
                    SELECT * FROM {cls.TABLE_NAME} 
                    WHERE user_id = ? AND homework_id = ?
                    ORDER BY created_at DESC
                """, (user_id, homework_id))
            else:
                results = db_manager.fetch_all(f"""
                    SELECT * FROM {cls.TABLE_NAME} 
                    WHERE user_id = ? ORDER BY created_at DESC
                """, (user_id,))
            
            assistance_list = []
            for result in results:
                assistance_list.append({
                    'id': result[0],
                    'user_id': result[1],
                    'homework_id': result[2],
                    'question_id': result[3],
                    'question_text': result[4],
                    'user_answer': result[5],
                    'correct_answer': result[6],
                    'analysis': result[7],
                    'hints': result[8],
                    'steps': result[9],
                    'score': result[10],
                    'max_score': result[11],
                    'status': result[12],
                    'created_at': result[13],
                    'updated_at': result[14]
                })
            return assistance_list
        except Exception as e:
            logger.error(f"获取用户作业辅导失败: {str(e)}")
            return []


class LearningAnalysis:
    """学习分析模型"""
    
    TABLE_NAME = 'learning_analysis'
    
    @classmethod
    def _create_table(cls):
        """创建学习分析表"""
        try:
            db_manager.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    analysis_type TEXT NOT NULL,
                    period TEXT NOT NULL,
                    metrics TEXT,
                    insights TEXT,
                    suggestions TEXT,
                    overall_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db_manager.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_analysis_user ON {cls.TABLE_NAME}(user_id)
            """)
        except Exception as e:
            logger.error(f"创建学习分析表失败: {str(e)}")
    
    @classmethod
    def create_analysis(cls, user_id: int, analysis_type: str, period: str, 
                        metrics: Dict, insights: str = '', 
                        suggestions: str = '', overall_score: float = 0.0) -> str:
        """创建学习分析"""
        cls._create_table()
        try:
            analysis_id = f"analysis_{uuid4().hex[:8]}"
            db_manager.execute(f"""
                INSERT INTO {cls.TABLE_NAME} 
                (id, user_id, analysis_type, period, metrics, insights, 
                 suggestions, overall_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (analysis_id, user_id, analysis_type, period, 
                  json.dumps(metrics), insights, suggestions, overall_score, 
                  datetime.now().isoformat()))
            return analysis_id
        except Exception as e:
            logger.error(f"创建学习分析失败: {str(e)}")
            return ''
    
    @classmethod
    def get_user_analysis(cls, user_id: int, analysis_type: str = None, limit: int = 10) -> List[Dict]:
        """获取用户学习分析"""
        try:
            if analysis_type:
                results = db_manager.fetch_all(f"""
                    SELECT * FROM {cls.TABLE_NAME} 
                    WHERE user_id = ? AND analysis_type = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (user_id, analysis_type, limit))
            else:
                results = db_manager.fetch_all(f"""
                    SELECT * FROM {cls.TABLE_NAME} 
                    WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
                """, (user_id, limit))
            
            analysis_list = []
            for result in results:
                analysis_list.append({
                    'id': result[0],
                    'user_id': result[1],
                    'analysis_type': result[2],
                    'period': result[3],
                    'metrics': json.loads(result[4]) if result[4] else {},
                    'insights': result[5],
                    'suggestions': result[6],
                    'overall_score': result[7],
                    'created_at': result[8]
                })
            return analysis_list
        except Exception as e:
            logger.error(f"获取用户学习分析失败: {str(e)}")
            return []


class AILearningAssistant:
    """智能学习助手服务"""
    
    def __init__(self):
        """初始化学习助手"""
        LearningRecommendation._create_table()
        HomeworkAssistant._create_table()
        LearningAnalysis._create_table()
        logger.info("[智能学习助手] 初始化完成")
    
    def generate_recommendations(self, user_id: int) -> List[Dict]:
        """生成学习推荐"""
        try:
            recommendations = []
            
            rec1 = LearningRecommendation.create(
                user_id=user_id,
                rec_type='knowledge_gap',
                content_id='math_algebra',
                content_type='course',
                title='代数基础强化',
                description='根据您的学习数据分析，建议加强代数基础知识的学习',
                confidence=0.85,
                priority=10
            )
            
            rec2 = LearningRecommendation.create(
                user_id=user_id,
                rec_type='practice',
                content_id='physics_mechanics',
                content_type='exercise',
                title='物理力学专项练习',
                description='推荐针对力学章节的专项练习题',
                confidence=0.78,
                priority=8
            )
            
            rec3 = LearningRecommendation.create(
                user_id=user_id,
                rec_type='review',
                content_id='history_modern',
                content_type='video',
                title='近代史重点回顾',
                description='根据遗忘曲线，建议复习近代史章节',
                confidence=0.72,
                priority=6
            )
            
            if rec1:
                recommendations.append({'id': rec1, 'type': 'knowledge_gap'})
            if rec2:
                recommendations.append({'id': rec2, 'type': 'practice'})
            if rec3:
                recommendations.append({'id': rec3, 'type': 'review'})
            
            logger.info(f"[智能学习助手] 为用户 {user_id} 生成 {len(recommendations)} 条推荐")
            return recommendations
        except Exception as e:
            logger.error(f"生成学习推荐失败: {str(e)}")
            return []
    
    def get_recommendations(self, user_id: int) -> List[Dict]:
        """获取用户推荐列表"""
        return LearningRecommendation.get_user_recommendations(user_id)
    
    def analyze_homework(self, user_id: int, homework_id: str, question_id: str,
                        question_text: str, user_answer: str) -> Dict:
        """分析作业答案"""
        try:
            assist_id = HomeworkAssistant.create_assistance(
                user_id=user_id,
                homework_id=homework_id,
                question_id=question_id,
                question_text=question_text,
                user_answer=user_answer
            )
            
            if not assist_id:
                raise BusinessException(message='创建作业辅导记录失败')
            
            hints = self._generate_hints(question_text, user_answer)
            steps = self._generate_solution_steps(question_text)
            
            HomeworkAssistant.update_assistance(
                assist_id,
                hints=json.dumps(hints),
                steps=json.dumps(steps),
                status='analyzed'
            )
            
            return {
                'assist_id': assist_id,
                'hints': hints,
                'steps': steps,
                'status': 'analyzed'
            }
        except Exception as e:
            logger.error(f"分析作业失败: {str(e)}")
            raise
    
    def _generate_hints(self, question_text: str, user_answer: str) -> List[str]:
        """生成提示"""
        hints = []
        
        if '解方程' in question_text or '方程' in question_text:
            hints.append('首先尝试将方程整理成标准形式 ax² + bx + c = 0')
            hints.append('考虑使用因式分解或求根公式')
        
        if '证明' in question_text:
            hints.append('回忆相关定理和公理')
            hints.append('尝试从结论反推')
        
        if '计算' in question_text or '求值' in question_text:
            hints.append('检查计算步骤是否正确')
            hints.append('注意单位换算和符号')
        
        if not hints:
            hints.append('仔细阅读题目，理解题意')
            hints.append('回忆相关知识点')
        
        return hints
    
    def _generate_solution_steps(self, question_text: str) -> List[str]:
        """生成解题步骤"""
        steps = []
        
        if '解方程' in question_text or '方程' in question_text:
            steps = [
                '步骤1: 整理方程，移项到左边',
                '步骤2: 化简方程',
                '步骤3: 使用合适的方法求解',
                '步骤4: 检验解是否正确'
            ]
        elif '证明' in question_text:
            steps = [
                '步骤1: 明确已知条件',
                '步骤2: 明确需要证明的结论',
                '步骤3: 寻找连接已知和结论的桥梁',
                '步骤4: 写出严谨的证明过程'
            ]
        else:
            steps = [
                '步骤1: 理解题目要求',
                '步骤2: 列出已知条件',
                '步骤3: 选择合适的方法',
                '步骤4: 逐步求解',
                '步骤5: 检查答案'
            ]
        
        return steps
    
    def generate_learning_report(self, user_id: int, period: str = 'week') -> Dict:
        """生成学习报告"""
        try:
            metrics = {
                'total_study_time': 1560,
                'completed_courses': 3,
                'completed_assignments': 8,
                'exam_scores': [85, 92, 78, 88],
                'average_score': 85.75,
                'improvement_rate': 12.5,
                'weak_points': ['代数', '几何', '物理'],
                'strong_points': ['语文', '英语'],
                'study_days': 6,
                'average_daily_time': 260
            }
            
            insights = self._generate_insights(metrics)
            suggestions = self._generate_suggestions(metrics)
            overall_score = self._calculate_overall_score(metrics)
            
            analysis_id = LearningAnalysis.create_analysis(
                user_id=user_id,
                analysis_type='comprehensive',
                period=period,
                metrics=metrics,
                insights=insights,
                suggestions=suggestions,
                overall_score=overall_score
            )
            
            return {
                'analysis_id': analysis_id,
                'period': period,
                'metrics': metrics,
                'insights': insights,
                'suggestions': suggestions,
                'overall_score': overall_score
            }
        except Exception as e:
            logger.error(f"生成学习报告失败: {str(e)}")
            raise
    
    def _generate_insights(self, metrics: Dict) -> str:
        """生成学习洞察"""
        insights = []
        
        if metrics.get('improvement_rate', 0) > 10:
            insights.append('🎉 学习进步明显，继续保持！')
        else:
            insights.append('💪 学习稳步进行中，可以尝试增加学习强度')
        
        if metrics.get('study_days', 0) >= 5:
            insights.append('⏰ 学习频率良好，养成了不错的学习习惯')
        
        weak_points = metrics.get('weak_points', [])
        if weak_points:
            insights.append(f'📚 薄弱环节: {", ".join(weak_points)}，建议针对性练习')
        
        strong_points = metrics.get('strong_points', [])
        if strong_points:
            insights.append(f'⭐ 强项: {", ".join(strong_points)}，可以尝试更有挑战性的内容')
        
        return '\n'.join(insights)
    
    def _generate_suggestions(self, metrics: Dict) -> str:
        """生成学习建议"""
        suggestions = []
        
        suggestions.append('📅 制定合理的学习计划，保持学习节奏')
        suggestions.append('🧠 定期复习已学内容，巩固记忆')
        suggestions.append('❓ 遇到问题及时寻求帮助，不要积累')
        suggestions.append('💡 尝试多种学习方法，找到最适合自己的方式')
        
        weak_points = metrics.get('weak_points', [])
        if weak_points:
            for point in weak_points[:2]:
                suggestions.append(f'🎯 针对「{point}」进行专项练习')
        
        return '\n'.join(suggestions)
    
    def _calculate_overall_score(self, metrics: Dict) -> float:
        """计算综合评分"""
        avg_score = metrics.get('average_score', 0)
        improvement = metrics.get('improvement_rate', 0)
        study_days = metrics.get('study_days', 0)
        
        score = (avg_score * 0.5) + (improvement * 0.3) + (study_days * 1.5)
        return min(round(score, 2), 100)
    
    def get_learning_analytics(self, user_id: int) -> Dict:
        """获取学习分析数据"""
        try:
            recommendations = self.get_recommendations(user_id)
            assistance_count = len(HomeworkAssistant.get_user_homework_assistance(user_id))
            recent_analysis = LearningAnalysis.get_user_analysis(user_id, limit=1)
            
            return {
                'recommendation_count': len(recommendations),
                'assistance_count': assistance_count,
                'recent_analysis': recent_analysis[0] if recent_analysis else None,
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取学习分析数据失败: {str(e)}")
            return {}


_ai_learning_assistant = None


def get_ai_learning_assistant() -> AILearningAssistant:
    """获取智能学习助手实例"""
    global _ai_learning_assistant
    if _ai_learning_assistant is None:
        _ai_learning_assistant = AILearningAssistant()
    return _ai_learning_assistant