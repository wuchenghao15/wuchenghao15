"""学习路径服务 - MTSCOS AI项目"""

from typing import List, Optional
from datetime import datetime
from app.models.learning_path import LearningPath, PathNode, LearningPathStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LearningPathService:
    """学习路径服务"""
    
    @staticmethod
    def create_path(user_id: int, name: str, description: str = None) -> LearningPath:
        """创建学习路径"""
        logger.info(f"创建学习路径: user_id={user_id}, name={name}")
        path = LearningPath.create(
            user_id=user_id,
            name=name,
            description=description
        )
        if path:
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
        if path and user_id and path.user_id != user_id:
            return None
        return path
    
    @staticmethod
    def add_node(path_id: int, title: str, order: int, description: str = None, 
                 node_type: str = 'lesson', content_url: str = None, 
                 estimated_time: int = None) -> PathNode:
        """添加路径节点"""
        logger.info(f"添加路径节点: path_id={path_id}, title={title}")
        return PathNode.create(
            path_id=path_id,
            node_order=order,
            title=title,
            description=description,
            node_type=node_type,
            content_url=content_url,
            estimated_time=estimated_time
        )
    
    @staticmethod
    def get_path_nodes(path_id: int) -> List[PathNode]:
        """获取路径所有节点"""
        return PathNode.get_by_path(path_id)
    
    @staticmethod
    def mark_node_completed(node_id: int) -> Optional[PathNode]:
        """标记节点完成"""
        logger.info(f"标记节点完成: node_id={node_id}")
        node = PathNode.mark_completed(node_id)
        
        if node:
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
    def generate_recommendation(user_id: int, subject: str = None) -> dict:
        """生成学习推荐"""
        logger.info(f"生成学习推荐: user_id={user_id}, subject={subject}")
        
        recommendation = {
            'user_id': user_id,
            'subject': subject or '综合',
            'recommended_topics': [],
            'estimated_time': 0,
            'next_steps': []
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