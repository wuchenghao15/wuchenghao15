"""学习路径服务 - MTSCOS AI项目"""

from typing import List, Optional
from datetime import datetime
from app.models.learning_path import LearningPath, PathNode, LearningPathStatus
from app.utils.logger import get_logger
from app.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    AuthorizationException,
    BusinessException
)

logger = get_logger(__name__)


class LearningPathService:
    """学习路径服务"""
    
    @staticmethod
    def create_path(user_id: int, name: str, description: str = None) -> LearningPath:
        """创建学习路径"""
        if not name or not name.strip():
            raise ValidationException(
                message='路径名称不能为空',
                field_errors={'name': '路径名称不能为空'}
            )
        
        logger.info(f"创建学习路径: user_id={user_id}, name={name}")
        path = LearningPath.create(
            user_id=user_id,
            name=name,
            description=description
        )
        
        if not path:
            raise BusinessException(
                message='学习路径创建失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        path.update(status=LearningPathStatus.ACTIVE)
        return path
    
    @staticmethod
    def get_user_paths(user_id: int, status: str = None) -> List[LearningPath]:
        """获取用户学习路径列表"""
        return LearningPath.get_by_user(user_id, status)
    
    @staticmethod
    def get_path(path_id: int, user_id: int = None) -> Optional[LearningPath]:
        """获取学习路径详情"""
        path = LearningPath.get_by_id(path_id)
        if not path:
            raise ResourceNotFoundException(
                message='学习路径不存在',
                resource_type='learning_path'
            )
        
        if user_id and path.user_id != user_id:
            raise AuthorizationException(
                message='无权访问此学习路径',
                suggestion='请联系路径创建者获取访问权限'
            )
        
        return path
    
    @staticmethod
    def add_node(path_id: int, title: str, order: int, description: str = None, 
                 node_type: str = 'lesson', content_url: str = None, 
                 estimated_time: int = None) -> PathNode:
        """添加路径节点"""
        if not title or not title.strip():
            raise ValidationException(
                message='节点标题不能为空',
                field_errors={'title': '节点标题不能为空'}
            )
        
        if order < 0:
            raise ValidationException(
                message='节点顺序必须大于等于0',
                field_errors={'order': '节点顺序必须大于等于0'}
            )
        
        if node_type not in ['lesson', 'quiz', 'practice', 'assessment', 'video']:
            raise ValidationException(
                message='无效的节点类型',
                field_errors={'node_type': '节点类型必须是: lesson, quiz, practice, assessment, video'}
            )
        
        path = LearningPath.get_by_id(path_id)
        if not path:
            raise ResourceNotFoundException(
                message='学习路径不存在',
                resource_type='learning_path'
            )
        
        logger.info(f"添加路径节点: path_id={path_id}, title={title}")
        node = PathNode.create(
            path_id=path_id,
            node_order=order,
            title=title,
            description=description,
            node_type=node_type,
            content_url=content_url,
            estimated_time=estimated_time
        )
        
        if not node:
            raise BusinessException(
                message='节点创建失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return node
    
    @staticmethod
    def get_path_nodes(path_id: int) -> List[PathNode]:
        """获取路径所有节点"""
        return PathNode.get_by_path(path_id)
    
    @staticmethod
    def mark_node_completed(node_id: int) -> Optional[PathNode]:
        """标记节点完成"""
        node = PathNode.get_by_id(node_id)
        if not node:
            raise ResourceNotFoundException(
                message='节点不存在',
                resource_type='path_node'
            )
        
        if node.completed:
            raise BusinessException(
                message='节点已完成',
                suggestion='该节点已经是完成状态，无需重复标记'
            )
        
        logger.info(f"标记节点完成: node_id={node_id}")
        node = PathNode.mark_completed(node_id)
        
        if not node:
            raise BusinessException(
                message='标记节点完成失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        LearningPathService._check_path_completion(node.path_id)
        return node
    
    @staticmethod
    def _check_path_completion(path_id: int):
        """检查路径是否完成"""
        path = LearningPath.get_by_id(path_id)
        if not path:
            return
        
        total_nodes = len(PathNode.get_by_path(path_id))
        completed_nodes = sum(1 for n in PathNode.get_by_path(path_id) if n.completed)
        
        if total_nodes > 0 and completed_nodes == total_nodes:
            path.update(status=LearningPathStatus.COMPLETED)
            logger.info(f"学习路径完成: path_id={path_id}")
    
    @staticmethod
    def calculate_progress(path_id: int) -> float:
        """计算学习进度"""
        nodes = PathNode.get_by_path(path_id)
        total_nodes = len(nodes)
        if total_nodes == 0:
            return 0.0
        
        completed_nodes = sum(1 for n in nodes if n.completed)
        return (completed_nodes / total_nodes) * 100
    
    @staticmethod
    def pause_path(path_id: int, user_id: int) -> Optional[LearningPath]:
        """暂停学习路径"""
        path = LearningPath.get_by_id(path_id)
        if not path:
            raise ResourceNotFoundException(
                message='学习路径不存在',
                resource_type='learning_path'
            )
        
        if path.user_id != user_id:
            raise AuthorizationException(
                message='无权操作此学习路径',
                suggestion='只有学习路径的创建者可以操作'
            )
        
        if path.status == LearningPathStatus.PAUSED:
            raise BusinessException(
                message='学习路径已暂停',
                suggestion='学习路径已经是暂停状态'
            )
        
        if path.status == LearningPathStatus.COMPLETED:
            raise BusinessException(
                message='学习路径已完成',
                suggestion='已完成的学习路径不能暂停'
            )
        
        logger.info(f"暂停学习路径: path_id={path_id}")
        path.update(status=LearningPathStatus.PAUSED)
        return LearningPath.get_by_id(path_id)
    
    @staticmethod
    def resume_path(path_id: int, user_id: int) -> Optional[LearningPath]:
        """恢复学习路径"""
        path = LearningPath.get_by_id(path_id)
        if not path:
            raise ResourceNotFoundException(
                message='学习路径不存在',
                resource_type='learning_path'
            )
        
        if path.user_id != user_id:
            raise AuthorizationException(
                message='无权操作此学习路径',
                suggestion='只有学习路径的创建者可以操作'
            )
        
        if path.status != LearningPathStatus.PAUSED:
            raise BusinessException(
                message='学习路径未暂停',
                suggestion='只有暂停状态的学习路径才能恢复'
            )
        
        logger.info(f"恢复学习路径: path_id={path_id}")
        path.update(status=LearningPathStatus.ACTIVE)
        return LearningPath.get_by_id(path_id)
    
    @staticmethod
    def delete_path(path_id: int, user_id: int) -> bool:
        """删除学习路径"""
        path = LearningPath.get_by_id(path_id)
        if not path:
            raise ResourceNotFoundException(
                message='学习路径不存在',
                resource_type='learning_path'
            )
        
        if path.user_id != user_id:
            raise AuthorizationException(
                message='无权删除此学习路径',
                suggestion='只有学习路径的创建者可以删除'
            )
        
        logger.info(f"删除学习路径: path_id={path_id}")
        if not LearningPath.delete(path_id):
            raise BusinessException(
                message='学习路径删除失败',
                suggestion='请稍后重试或联系管理员'
            )
        
        return True
    
    @staticmethod
    def get_learning_statistics(user_id: int) -> dict:
        """获取用户学习统计"""
        paths = LearningPath.get_by_user(user_id)
        
        total_paths = len(paths)
        completed_paths = sum(1 for p in paths if p.status == LearningPathStatus.COMPLETED)
        active_paths = sum(1 for p in paths if p.status == LearningPathStatus.ACTIVE)
        paused_paths = sum(1 for p in paths if p.status == LearningPathStatus.PAUSED)
        
        total_nodes = 0
        completed_nodes = 0
        
        for path in paths:
            nodes = PathNode.get_by_path(path.id)
            total_nodes += len(nodes)
            completed_nodes += sum(1 for n in nodes if n.completed)
        
        avg_progress = (completed_nodes / total_nodes) * 100 if total_nodes > 0 else 0
        
        return {
            'user_id': user_id,
            'total_paths': total_paths,
            'completed_paths': completed_paths,
            'active_paths': active_paths,
            'paused_paths': paused_paths,
            'total_nodes': total_nodes,
            'completed_nodes': completed_nodes,
            'avg_progress': round(avg_progress, 2),
            'completion_rate': round((completed_paths / total_paths) * 100, 2) if total_paths > 0 else 0
        }
    
    @staticmethod
    def get_learning_trend(user_id: int, days: int = 7) -> dict:
        """获取用户学习趋势"""
        from datetime import datetime, timedelta
        
        trend_data = []
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            trend_data.append({
                'date': date_str,
                'completed_nodes': 0,
                'time_spent': 0
            })
        
        return {
            'user_id': user_id,
            'days': days,
            'trend_data': trend_data,
            'summary': {
                'total_completed': sum(d['completed_nodes'] for d in trend_data),
                'avg_daily': sum(d['completed_nodes'] for d in trend_data) / days if days > 0 else 0
            }
        }
    
    @staticmethod
    def get_next_node(path_id: int) -> Optional[PathNode]:
        """获取下一个待完成的节点"""
        nodes = PathNode.get_by_path(path_id)
        
        for node in nodes:
            if not node.completed:
                return node
        
        return None
    
    @staticmethod
    def generate_recommendation(user_id: int, subject: str = None) -> dict:
        """生成学习推荐"""
        logger.info(f"生成学习推荐: user_id={user_id}, subject={subject}")
        
        recommendation = {
            'user_id': user_id,
            'subject': subject or '综合',
            'recommended_topics': [],
            'estimated_time': 0,
            'next_steps': [],
            'learning_statistics': LearningPathService.get_learning_statistics(user_id)
        }
        
        if subject == 'math':
            recommendation['recommended_topics'] = [
                {'topic': '代数基础', 'priority': 1},
                {'topic': '几何入门', 'priority': 2},
                {'topic': '函数概念', 'priority': 3}
            ]
            recommendation['estimated_time'] = 120
        elif subject == 'english':
            recommendation['recommended_topics'] = [
                {'topic': '词汇积累', 'priority': 1},
                {'topic': '语法基础', 'priority': 2},
                {'topic': '阅读理解', 'priority': 3}
            ]
            recommendation['estimated_time'] = 90
        else:
            recommendation['recommended_topics'] = [
                {'topic': '基础知识巩固', 'priority': 1},
                {'topic': '专项技能提升', 'priority': 2},
                {'topic': '综合能力测试', 'priority': 3}
            ]
            recommendation['estimated_time'] = 150
        
        recommendation['next_steps'] = [
            '完成当前节点学习',
            '进行章节测试',
            '查看学习报告'
        ]
        
        return recommendation