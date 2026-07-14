# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI系统 V2.0 (AI System)
增强版AI系统，支持多引擎管理、自动学习、智能问答和任务分发
"""

import time
import uuid
import json
import logging
import threading
import sqlite3
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AISystem')

class AIEngineType(Enum):
    """AI引擎类型枚举"""
    TEACHER = "teacher"
    RESEARCHER = "researcher"
    EXPERT = "expert"
    STUDENT = "student"
    ENGINEER = "engineer"
    ARTIST = "artist"
    ARDUINO = "arduino"
    MAINTENANCE = "maintenance"
    USER = "user"
    BUTLER = "butler"

class LearningLevel(Enum):
    """学习等级枚举"""
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AIEngineConfig:
    """AI引擎配置"""
    engine_id: str
    engine_type: AIEngineType
    name: str
    description: str = ""
    enabled: bool = True
    max_concurrent_tasks: int = 5
    learning_rate: float = 0.1
    target_accuracy: float = 0.95
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class AIEngineState:
    """AI引擎状态"""
    engine_id: str
    status: str = "idle"
    learning_level: LearningLevel = LearningLevel.NOVICE
    accuracy: float = 0.8
    total_interactions: int = 0
    correct_responses: int = 0
    last_updated: float = 0.0
    current_tasks: int = 0
    
    def __post_init__(self):
        if self.last_updated == 0.0:
            self.last_updated = time.time()

@dataclass
class AITask:
    """AI任务"""
    task_id: str
    engine_id: str
    prompt: str
    context: Dict = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class KnowledgeItem:
    """知识项"""
    knowledge_id: str
    category: str
    content: str
    metadata: Dict = None
    created_at: float = 0.0
    accessed_count: int = 0
    last_accessed_at: Optional[float] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

class AISystem:
    """增强版AI系统"""
    
    def __init__(self):
        """初始化AI系统"""
        self.engines: Dict[str, AIEngineConfig] = {}
        self.engine_states: Dict[str, AIEngineState] = {}
        self.tasks: Dict[str, AITask] = {}
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        
        self.task_queue = deque()
        self.task_results = {}
        
        self.lock = threading.Lock()
        self.learning_lock = threading.Lock()
        
        self._init_database()
        self._init_engines()
        
        self._start_task_processor()
        self._start_learning_monitor()
        
        logger.info("AI系统初始化完成")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_conn = sqlite3.connect('ai_system.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_engines (
                    engine_id TEXT PRIMARY KEY,
                    engine_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    max_concurrent_tasks INTEGER DEFAULT 5,
                    learning_rate REAL DEFAULT 0.1,
                    target_accuracy REAL DEFAULT 0.95,
                    created_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS engine_states (
                    engine_id TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'idle',
                    learning_level TEXT DEFAULT 'novice',
                    accuracy REAL DEFAULT 0.8,
                    total_interactions INTEGER DEFAULT 0,
                    correct_responses INTEGER DEFAULT 0,
                    last_updated REAL,
                    FOREIGN KEY (engine_id) REFERENCES ai_engines(engine_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_tasks (
                    task_id TEXT PRIMARY KEY,
                    engine_id TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    context TEXT,
                    priority INTEGER DEFAULT 2,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    error TEXT,
                    created_at REAL,
                    started_at REAL,
                    completed_at REAL,
                    FOREIGN KEY (engine_id) REFERENCES ai_engines(engine_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    knowledge_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL,
                    accessed_count INTEGER DEFAULT 0,
                    last_accessed_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_history (
                    history_id TEXT PRIMARY KEY,
                    engine_id TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    feedback INTEGER DEFAULT 0,
                    timestamp REAL,
                    FOREIGN KEY (engine_id) REFERENCES ai_engines(engine_id)
                )
            ''')
            
            self.db_conn.commit()
            logger.info("AI系统数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def _init_engines(self):
        """初始化默认AI引擎"""
        engine_configs = [
            AIEngineConfig("eng_teacher", AIEngineType.TEACHER, "教师AI", "个性化教学指导"),
            AIEngineConfig("eng_researcher", AIEngineType.RESEARCHER, "教研员AI", "课程设计与题库优化"),
            AIEngineConfig("eng_expert", AIEngineType.EXPERT, "专家AI", "专业分析与职业咨询"),
            AIEngineConfig("eng_student", AIEngineType.STUDENT, "学生AI", "学习辅助与作业指导"),
            AIEngineConfig("eng_engineer", AIEngineType.ENGINEER, "工程师AI", "系统架构与代码审查"),
            AIEngineConfig("eng_artist", AIEngineType.ARTIST, "艺术家AI", "UI/UX设计与创意生成"),
            AIEngineConfig("eng_arduino", AIEngineType.ARDUINO, "Arduino设计AI", "硬件设计与代码生成"),
            AIEngineConfig("eng_maintenance", AIEngineType.MAINTENANCE, "维护AI", "系统维护与故障排除"),
            AIEngineConfig("eng_user", AIEngineType.USER, "用户AI", "行为分析与个性化推荐"),
            AIEngineConfig("eng_butler", AIEngineType.BUTLER, "管家AI", "智能助手与任务管理")
        ]
        
        with self.lock:
            for config in engine_configs:
                if config.engine_id not in self.engines:
                    self.engines[config.engine_id] = config
                    self.engine_states[config.engine_id] = AIEngineState(config.engine_id)
                    self._save_engine(config)
                    self._save_engine_state(self.engine_states[config.engine_id])
    
    def _save_engine(self, config: AIEngineConfig):
        """保存引擎配置到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO ai_engines
                (engine_id, engine_type, name, description, enabled, max_concurrent_tasks, 
                 learning_rate, target_accuracy, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                config.engine_id,
                config.engine_type.value,
                config.name,
                config.description,
                config.enabled,
                config.max_concurrent_tasks,
                config.learning_rate,
                config.target_accuracy,
                config.created_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存引擎配置失败: {str(e)}")
    
    def _save_engine_state(self, state: AIEngineState):
        """保存引擎状态到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO engine_states
                (engine_id, status, learning_level, accuracy, total_interactions, 
                 correct_responses, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                state.engine_id,
                state.status,
                state.learning_level.value,
                state.accuracy,
                state.total_interactions,
                state.correct_responses,
                state.last_updated
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存引擎状态失败: {str(e)}")
    
    def add_engine(self, engine_type: AIEngineType, name: str, description: str = "",
                  max_concurrent_tasks: int = 5) -> str:
        """添加新AI引擎"""
        engine_id = f"eng_{uuid.uuid4().hex[:8]}"
        
        config = AIEngineConfig(
            engine_id=engine_id,
            engine_type=engine_type,
            name=name,
            description=description,
            max_concurrent_tasks=max_concurrent_tasks
        )
        
        with self.lock:
            self.engines[engine_id] = config
            self.engine_states[engine_id] = AIEngineState(engine_id)
            self._save_engine(config)
            self._save_engine_state(self.engine_states[engine_id])
        
        logger.info(f"添加AI引擎: {name} ({engine_id})")
        return engine_id
    
    def get_engine(self, engine_id: str) -> Optional[AIEngineConfig]:
        """获取引擎配置"""
        with self.lock:
            return self.engines.get(engine_id)
    
    def list_engines(self) -> List[Dict]:
        """列出所有引擎"""
        with self.lock:
            result = []
            for engine_id, config in self.engines.items():
                state = self.engine_states.get(engine_id)
                result.append({
                    "engine_id": config.engine_id,
                    "engine_type": config.engine_type.value,
                    "name": config.name,
                    "description": config.description,
                    "enabled": config.enabled,
                    "status": state.status if state else "unknown",
                    "learning_level": state.learning_level.value if state else "novice",
                    "accuracy": state.accuracy if state else 0.0,
                    "total_interactions": state.total_interactions if state else 0
                })
            return result
    
    def enable_engine(self, engine_id: str) -> bool:
        """启用引擎"""
        with self.lock:
            config = self.engines.get(engine_id)
            if not config:
                return False
            config.enabled = True
            self._save_engine(config)
        
        logger.info(f"启用AI引擎: {engine_id}")
        return True
    
    def disable_engine(self, engine_id: str) -> bool:
        """禁用引擎"""
        with self.lock:
            config = self.engines.get(engine_id)
            if not config:
                return False
            config.enabled = False
            self._save_engine(config)
        
        logger.info(f"禁用AI引擎: {engine_id}")
        return True
    
    def submit_task(self, engine_id: str, prompt: str, context: Dict = None,
                   priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """提交AI任务"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = AITask(
            task_id=task_id,
            engine_id=engine_id,
            prompt=prompt,
            context=context,
            priority=priority
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.task_queue.append((priority.value, task_id))
            self._save_task(task)
        
        logger.debug(f"提交AI任务: {task_id} -> {engine_id}")
        return task_id
    
    def _save_task(self, task: AITask):
        """保存任务到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO ai_tasks
                (task_id, engine_id, prompt, context, priority, status, result, error, 
                 created_at, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_id,
                task.engine_id,
                task.prompt,
                json.dumps(task.context) if task.context else None,
                task.priority.value,
                task.status.value,
                json.dumps(task.result) if task.result else None,
                task.error,
                task.created_at,
                task.started_at,
                task.completed_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存任务失败: {str(e)}")
    
    def _start_task_processor(self):
        """启动任务处理线程"""
        self.task_processor = threading.Thread(
            target=self._task_processor_loop,
            name="ai_task_processor",
            daemon=True
        )
        self.task_processor.start()
    
    def _task_processor_loop(self):
        """任务处理循环"""
        while True:
            try:
                if self.task_queue:
                    self._process_next_task()
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"任务处理线程错误: {str(e)}")
                time.sleep(1)
    
    def _process_next_task(self):
        """处理下一个任务"""
        with self.lock:
            if not self.task_queue:
                return
            
            priority, task_id = self.task_queue.popleft()
            task = self.tasks.get(task_id)
            
            if not task:
                return
            
            engine_config = self.engines.get(task.engine_id)
            engine_state = self.engine_states.get(task.engine_id)
            
            if not engine_config or not engine_state:
                task.status = TaskStatus.FAILED
                task.error = "引擎不存在"
                return
            
            if not engine_config.enabled:
                task.status = TaskStatus.FAILED
                task.error = "引擎已禁用"
                return
            
            if engine_state.current_tasks >= engine_config.max_concurrent_tasks:
                self.task_queue.append((priority, task_id))
                return
            
            engine_state.status = "running"
            engine_state.current_tasks += 1
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
        
        result = self._execute_task(task, engine_config, engine_state)
        
        with self.lock:
            task.completed_at = time.time()
            task.result = result
            task.status = TaskStatus.COMPLETED
            
            engine_state.status = "idle"
            engine_state.current_tasks -= 1
            engine_state.total_interactions += 1
            
            self._save_task(task)
            self._save_engine_state(engine_state)
        
        logger.debug(f"任务完成: {task_id}")
    
    def _execute_task(self, task: AITask, engine_config: AIEngineConfig, 
                      engine_state: AIEngineState) -> Dict:
        """执行AI任务"""
        time.sleep(0.5)
        
        mock_responses = {
            AIEngineType.TEACHER: {"answer": f"针对你的问题：{task.prompt}，我建议...", "confidence": engine_state.accuracy},
            AIEngineType.RESEARCHER: {"analysis": f"分析问题：{task.prompt}，结论如下...", "confidence": engine_state.accuracy},
            AIEngineType.EXPERT: {"advice": f"专业建议：{task.prompt}，我的建议是...", "confidence": engine_state.accuracy},
            AIEngineType.STUDENT: {"guidance": f"学习指导：{task.prompt}，你可以这样学习...", "confidence": engine_state.accuracy},
            AIEngineType.ENGINEER: {"design": f"架构设计：{task.prompt}，设计方案如下...", "confidence": engine_state.accuracy},
            AIEngineType.ARTIST: {"design": f"创意设计：{task.prompt}，设计思路如下...", "confidence": engine_state.accuracy},
            AIEngineType.ARDUINO: {"code": f"Arduino代码：{task.prompt}，代码如下...", "confidence": engine_state.accuracy},
            AIEngineType.MAINTENANCE: {"solution": f"维护方案：{task.prompt}，解决方案如下...", "confidence": engine_state.accuracy},
            AIEngineType.USER: {"analysis": f"用户分析：{task.prompt}，分析结果如下...", "confidence": engine_state.accuracy},
            AIEngineType.BUTLER: {"assistance": f"管家服务：{task.prompt}，已为你安排...", "confidence": engine_state.accuracy}
        }
        
        return mock_responses.get(engine_config.engine_type, {"result": "处理完成"})
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            return {
                "task_id": task.task_id,
                "engine_id": task.engine_id,
                "prompt": task.prompt,
                "priority": task.priority.name,
                "status": task.status.value,
                "result": task.result,
                "error": task.error,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "duration": task.completed_at - task.started_at if task.started_at and task.completed_at else None
            }
    
    def provide_feedback(self, task_id: str, rating: float):
        """提供任务反馈（用于自动学习）"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
            
            engine_state = self.engine_states.get(task.engine_id)
            if not engine_state:
                return
            
            engine_state.total_interactions += 1
            if rating >= 0.7:
                engine_state.correct_responses += 1
            
            engine_state.accuracy = engine_state.correct_responses / engine_state.total_interactions
            engine_state.last_updated = time.time()
            
            self._update_learning_level(engine_state)
            self._save_engine_state(engine_state)
            
            self._record_learning_history(task, rating)
    
    def _update_learning_level(self, state: AIEngineState):
        """更新学习等级"""
        if state.accuracy >= 0.95:
            state.learning_level = LearningLevel.MASTER
        elif state.accuracy >= 0.9:
            state.learning_level = LearningLevel.EXPERT
        elif state.accuracy >= 0.8:
            state.learning_level = LearningLevel.ADVANCED
        elif state.accuracy >= 0.7:
            state.learning_level = LearningLevel.INTERMEDIATE
        else:
            state.learning_level = LearningLevel.NOVICE
    
    def _record_learning_history(self, task: AITask, rating: float):
        """记录学习历史"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO learning_history
                (history_id, engine_id, prompt, response, feedback, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f"hist_{uuid.uuid4().hex[:8]}",
                task.engine_id,
                task.prompt,
                json.dumps(task.result) if task.result else "",
                rating,
                time.time()
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"记录学习历史失败: {str(e)}")
    
    def add_knowledge(self, category: str, content: str, metadata: Dict = None) -> str:
        """添加知识项"""
        knowledge_id = f"k_{uuid.uuid4().hex[:8]}"
        
        knowledge = KnowledgeItem(
            knowledge_id=knowledge_id,
            category=category,
            content=content,
            metadata=metadata
        )
        
        with self.lock:
            self.knowledge_base[knowledge_id] = knowledge
            self._save_knowledge(knowledge)
        
        logger.info(f"添加知识项: {category} ({knowledge_id})")
        return knowledge_id
    
    def _save_knowledge(self, knowledge: KnowledgeItem):
        """保存知识项到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO knowledge_base
                (knowledge_id, category, content, metadata, created_at, accessed_count, last_accessed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge.knowledge_id,
                knowledge.category,
                knowledge.content,
                json.dumps(knowledge.metadata) if knowledge.metadata else None,
                knowledge.created_at,
                knowledge.accessed_count,
                knowledge.last_accessed_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存知识项失败: {str(e)}")
    
    def search_knowledge(self, query: str, category: str = None) -> List[Dict]:
        """搜索知识库"""
        results = []
        
        with self.lock:
            for knowledge in self.knowledge_base.values():
                if category and knowledge.category != category:
                    continue
                
                if query.lower() in knowledge.content.lower() or \
                   query.lower() in knowledge.category.lower():
                    knowledge.accessed_count += 1
                    knowledge.last_accessed_at = time.time()
                    results.append({
                        "knowledge_id": knowledge.knowledge_id,
                        "category": knowledge.category,
                        "content": knowledge.content,
                        "metadata": knowledge.metadata,
                        "accessed_count": knowledge.accessed_count
                    })
        
        results.sort(key=lambda x: x["accessed_count"], reverse=True)
        return results[:10]
    
    def _start_learning_monitor(self):
        """启动学习监控线程"""
        self.learning_monitor = threading.Thread(
            target=self._learning_monitor_loop,
            name="ai_learning_monitor",
            daemon=True
        )
        self.learning_monitor.start()
    
    def _learning_monitor_loop(self):
        """学习监控循环"""
        while True:
            try:
                self._update_engine_learning()
                time.sleep(60)
            except Exception as e:
                logger.error(f"学习监控线程错误: {str(e)}")
                time.sleep(60)
    
    def _update_engine_learning(self):
        """更新引擎学习状态"""
        with self.lock:
            for engine_id, state in self.engine_states.items():
                config = self.engines.get(engine_id)
                if not config:
                    continue
                
                if state.accuracy < config.target_accuracy:
                    improvement = config.learning_rate * (config.target_accuracy - state.accuracy)
                    state.accuracy = min(state.accuracy + improvement, config.target_accuracy)
                    self._update_learning_level(state)
                    self._save_engine_state(state)
    
    def ask(self, prompt: str, context: Dict = None, engine_type: AIEngineType = None) -> Dict:
        """智能问答接口"""
        if engine_type:
            engine_id = next((eid for eid, config in self.engines.items() 
                            if config.engine_type == engine_type and config.enabled), None)
        else:
            engine_id = self._select_best_engine(prompt)
        
        if not engine_id:
            return {"error": "没有可用的AI引擎"}
        
        task_id = self.submit_task(engine_id, prompt, context)
        
        while True:
            status = self.get_task_status(task_id)
            if status["status"] in ["completed", "failed"]:
                return status
            time.sleep(0.1)
    
    def _select_best_engine(self, prompt: str) -> Optional[str]:
        """根据问题选择最佳引擎"""
        keywords = {
            AIEngineType.TEACHER: ["学习", "课程", "教学", "讲解", "作业"],
            AIEngineType.RESEARCHER: ["研究", "设计", "分析", "题库", "教研"],
            AIEngineType.EXPERT: ["专业", "咨询", "建议", "分析", "指导"],
            AIEngineType.STUDENT: ["学生", "作业", "考试", "复习", "练习"],
            AIEngineType.ENGINEER: ["代码", "架构", "设计", "开发", "bug"],
            AIEngineType.ARTIST: ["设计", "创意", "UI", "视觉", "艺术"],
            AIEngineType.ARDUINO: ["硬件", "电路", "Arduino", "传感器"],
            AIEngineType.MAINTENANCE: ["维护", "故障", "修复", "优化"],
            AIEngineType.USER: ["用户", "分析", "推荐", "行为"],
            AIEngineType.BUTLER: ["任务", "管理", "提醒", "安排"]
        }
        
        prompt_lower = prompt.lower()
        best_engine = None
        best_score = 0
        
        for engine_type, kw_list in keywords.items():
            score = sum(1 for kw in kw_list if kw in prompt_lower)
            if score > best_score:
                best_score = score
                best_engine = engine_type
        
        if best_engine:
            return next((eid for eid, config in self.engines.items() 
                        if config.engine_type == best_engine and config.enabled), None)
        
        return next((eid for eid, config in self.engines.items() if config.enabled), None)
    
    def get_stats(self) -> Dict:
        """获取AI系统统计信息"""
        with self.lock:
            total_tasks = len(self.tasks)
            completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
            pending_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
            
            avg_accuracy = 0
            active_engines = 0
            for state in self.engine_states.values():
                avg_accuracy += state.accuracy
                if state.status == "running":
                    active_engines += 1
            
            if self.engine_states:
                avg_accuracy /= len(self.engine_states)
            
            return {
                "total_engines": len(self.engines),
                "enabled_engines": sum(1 for e in self.engines.values() if e.enabled),
                "active_engines": active_engines,
                "avg_engine_accuracy": avg_accuracy,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
                "total_knowledge_items": len(self.knowledge_base),
                "task_queue_size": len(self.task_queue)
            }


def test_ai_system():
    """测试AI系统"""
    print("AI系统 V2.0 测试")
    print("=" * 60)
    
    ai = AISystem()
    
    print("列出AI引擎:")
    engines = ai.list_engines()
    for engine in engines:
        print(f"  {engine['name']}: {engine['learning_level']}, 准确率: {engine['accuracy']:.2%}")
    
    print("\n提交测试任务:")
    task1 = ai.submit_task("eng_teacher", "如何提高数学成绩？", {"subject": "math"}, TaskPriority.HIGH)
    task2 = ai.submit_task("eng_expert", "职业发展规划建议", {"user_role": "student"}, TaskPriority.NORMAL)
    task3 = ai.submit_task("eng_engineer", "如何设计一个高性能的Web系统？", {}, TaskPriority.HIGH)
    
    print(f"  已提交任务: {task1}, {task2}, {task3}")
    
    print("\n等待任务完成...")
    time.sleep(2)
    
    print("\n任务状态:")
    for task_id in [task1, task2, task3]:
        status = ai.get_task_status(task_id)
        print(f"  {task_id}: {status['status']}, 引擎: {status['engine_id']}")
        if status['result']:
            print(f"    结果类型: {list(status['result'].keys())[0]}")
    
    print("\n提供任务反馈:")
    ai.provide_feedback(task1, 0.9)
    ai.provide_feedback(task2, 0.85)
    ai.provide_feedback(task3, 0.95)
    print("  反馈已提交")
    
    print("\n智能问答:")
    result = ai.ask("如何备考公务员考试？")
    print(f"  问题: 如何备考公务员考试？")
    print(f"  使用引擎: {result['engine_id']}")
    print(f"  状态: {result['status']}")
    
    print("\n添加知识项:")
    ai.add_knowledge("学习方法", "费曼学习法：用简单的语言解释复杂的概念")
    ai.add_knowledge("学习方法", "番茄工作法：25分钟专注+5分钟休息")
    ai.add_knowledge("考试技巧", "先易后难，合理分配答题时间")
    print("  已添加3条知识")
    
    print("\n搜索知识库:")
    results = ai.search_knowledge("学习")
    for result in results:
        print(f"  {result['category']}: {result['content'][:30]}...")
    
    print("\n系统统计:")
    stats = ai.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nAI系统 V2.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_ai_system()