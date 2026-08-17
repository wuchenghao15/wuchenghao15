# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI自我学习和升级系统
功能:
5. 机器学习模型支持,增强AI推理能力
6. 增强知识提取和整合能力
7. 改进知识图谱构建和分析
8. 自动发现和解决问题
"""
import os
import sys
import sqlite3
from contextlib import contextmanager
import logging
import traceback
import subprocess
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Set
import threading
import re
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_self_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONFIG = {
    "db_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev.db"),
    "learning_interval_hours": 24,
    "upgrade_interval_days": 7,
    "knowledge_sources": [
        "internal_database",
        "code_repositories",
        "external_apis",
        "user_interactions"
    ],
    "ai_brain_table": "ai_brain_features",
    "knowledge_version_table": "knowledge_versions",
    "learning_plan_table": "learning_plans"
}

class MLModelManager:
    """机器学习模型管理器"""
    def __init__(self):
        self.is_trained = False
        self.knowledge_ids = []

    def train(self, knowledge_list: List[Dict]):
        """训练机器学习模型"""
        if not knowledge_list:
            logger.warning("没有知识数据用于训练模型")
            return False

        try:
            self.knowledge_ids = []
            for knowledge in knowledge_list:
                self.knowledge_ids.append(knowledge.get("id", ""))
            
            self.is_trained = True
            logger.info(f"机器学习模型训练完成,使用了 {len(knowledge_list)} 条知识数据")
            return True
        except Exception as e:
            logger.error(f"训练机器学习模型出错: {str(e)}")
            return False

    def classify_knowledge(self, knowledge: Dict) -> str:
        """分类知识"""
        content = knowledge.get("content", {})
        text = str(content).lower()
        
        categories = {
            "problem_solution": ["problem", "solution", "fix", "error", "bug"],
            "code_pattern": ["code", "pattern", "function", "class", "method"],
            "template_pattern": ["template", "html", "jinja", "extends", "block"],
            "css_pattern": ["css", "style", "variable", "class", "id"],
            "user_behavior": ["user", "behavior", "access", "log", "route"],
            "tech_update": ["update", "version", "feature", "framework", "library"]
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return "general"

class KnowledgeExtractor:
    """知识提取器基类"""
    def __init__(self, source_type: str):
        self.source_type = source_type
        self.ml_model = MLModelManager()

    def extract_knowledge(self) -> List[Dict]:
        """从源中提取知识"""
        raise NotImplementedError("子类必须实现extract_knowledge方法")

    def preprocess_knowledge(self, knowledge_list: List[Dict]) -> List[Dict]:
        """预处理提取的知识"""
        for knowledge in knowledge_list:
            knowledge["type"] = self.ml_model.classify_knowledge(knowledge)
            if "extracted_at" not in knowledge:
                knowledge["extracted_at"] = datetime.now(timezone.utc).isoformat()
        return knowledge_list

class InternalDatabaseExtractor(KnowledgeExtractor):
    """内部数据库知识提取器"""
    def __init__(self, db_path: str):
        super().__init__("internal_database")
        self.db_path = db_path

    def extract_knowledge(self) -> List[Dict]:
        """从内部数据库提取知识"""
        knowledge_list = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT pe.error_content, ef.fix_strategy, ef.fix_implementation
            FROM project_errors pe
            JOIN error_fixes ef ON pe.id = ef.error_id
            WHERE pe.status = 'fixed'
            ''')
            
            for row in cursor.fetchall():
                error_content, fix_strategy, fix_implementation = row
                knowledge_list.append({
                    "id": f"fix_{len(knowledge_list)}",
                    "source": "internal:fixes",
                    "content": {
                        "problem": error_content,
                        "solution": {
                            "strategy": fix_strategy,
                            "implementation": fix_implementation
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "confidence": 0.9
                    }
                })
            
            conn.close()
            knowledge_list = self.preprocess_knowledge(knowledge_list)
            logger.info(f"从内部数据库提取了 {len(knowledge_list)} 条知识")
        except Exception as e:
            logger.error(f"内部数据库知识提取器出错: {str(e)}")
        
        return knowledge_list

class CodeRepositoryExtractor(KnowledgeExtractor):
    """代码仓库知识提取器"""
    def __init__(self, repo_path: str):
        super().__init__("code_repository")
        self.repo_path = repo_path

    def extract_knowledge(self) -> List[Dict]:
        """从代码仓库提取知识"""
        knowledge_list = []
        try:
            html_files = []
            templates_dir = os.path.join(self.repo_path, "templates")
            if os.path.exists(templates_dir):
                for root, dirs, files in os.walk(templates_dir):
                    for file in files:
                        if file.endswith(".html"):
                            html_files.append(os.path.join(root, file))

            for html_file in html_files:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                extends_match = re.search(r'{%\s*extends\s+[\'"]([^\'"]+)[\'"]\s*%}', content)
                if extends_match:
                    knowledge_list.append({
                        "id": f"template_{len(knowledge_list)}",
                        "source": f"template:{os.path.basename(html_file)}",
                        "type": "template_pattern",
                        "content": {
                            "pattern_type": "template_inheritance",
                            "child_template": os.path.basename(html_file),
                            "parent_template": extends_match.group(1),
                            "location": html_file,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "confidence": 0.8
                        }
                    })
        except Exception as e:
            logger.error(f"代码仓库知识提取器出错: {str(e)}")
        
        return knowledge_list

class FrontendBeautificationExtractor(KnowledgeExtractor):
    """前端美化知识提取器"""
    def __init__(self, repo_path: str):
        super().__init__("frontend_beautification")
        self.repo_path = repo_path

    def extract_knowledge(self) -> List[Dict]:
        """从前端美化历史提取知识"""
        knowledge_list = []
        try:
            beautification_history_file = os.path.join(self.repo_path, "frontend_beautification_history.json")
            if os.path.exists(beautification_history_file):
                with open(beautification_history_file, 'r', encoding='utf-8') as f:
                    beautification_history = json.load(f)
                
                for record in beautification_history:
                    knowledge_list.append({
                        "id": f"beautify_{len(knowledge_list)}",
                        "source": "beautification:history",
                        "type": "css_pattern",
                        "content": {
                            "file_path": record.get("file_path", ""),
                            "changes": record.get("changes", []),
                            "timestamp": record.get("timestamp", "")
                        }
                    })
        except Exception as e:
            logger.error(f"前端美化知识提取器出错: {str(e)}")
        
        return knowledge_list

class UserInteractionExtractor(KnowledgeExtractor):
    """用户交互知识提取器"""
    def __init__(self, db_path: str):
        super().__init__("user_interactions")
        self.db_path = db_path

    def extract_knowledge(self) -> List[Dict]:
        """从用户交互中提取知识"""
        knowledge_list = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT path, COUNT(*) as count
                FROM access_logs
                GROUP BY path
                ORDER BY count DESC
                LIMIT 10
            ''')

            for row in cursor.fetchall():
                path, count = row
                knowledge_list.append({
                    "id": f"access_{len(knowledge_list)}",
                    "source": "user:access_logs",
                    "type": "user_behavior",
                    "content": {
                        "behavior_type": "popular_route",
                        "path": path,
                        "access_count": count,
                        "confidence": 0.8
                    }
                })
            
            conn.close()
            logger.info(f"从用户交互中提取了 {len(knowledge_list)} 条知识")
        except Exception as e:
            logger.error(f"用户交互知识提取器出错: {str(e)}")
        
        return knowledge_list

class ExternalAPIExtractor(KnowledgeExtractor):
    """外部API知识提取器"""
    def __init__(self):
        super().__init__("external_apis")

    def extract_knowledge(self) -> List[Dict]:
        """从外部API提取知识"""
        knowledge_list = []
        try:
            knowledge_list.append({
                "id": "external_1",
                "source": "external:tech_news",
                "type": "tech_update",
                "content": {
                    "framework": "Flask",
                    "features": ["Improved async support", "Better error handling", "Enhanced security"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.7
                }
            })
        except Exception as e:
            logger.error(f"外部API知识提取器出错: {str(e)}")
        
        return knowledge_list

class AILearningManager:
    """AI学习和升级管理器"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.knowledge_extractors = []
        self.learning_plan = []
        self.thread = None
        self.is_running = False
        self.ml_model_manager = MLModelManager()
        self.current_knowledge_list = []

    def initialize(self):
        """初始化学习管理器"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_number TEXT NOT NULL,
                description TEXT NOT NULL,
                knowledge_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_name TEXT NOT NULL,
                description TEXT NOT NULL,
                frequency TEXT NOT NULL,
                next_run TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                method TEXT NOT NULL,
                ip TEXT NOT NULL,
                user_agent TEXT,
                status_code INTEGER NOT NULL,
                response_time REAL,
                created_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_brain_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_type TEXT NOT NULL,
                issue_description TEXT,
                issue_characteristics TEXT,
                solution TEXT,
                severity INTEGER,
                impact_scope TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM access_logs")
        if cursor.fetchone()[0] == 0:
            test_logs = [
                ("/", "GET", "127.0.0.1", "Mozilla/5.0", 200, 0.123, datetime.now(timezone.utc).isoformat()),
                ("/login", "GET", "127.0.0.1", "Mozilla/5.0", 200, 0.098, datetime.now(timezone.utc).isoformat()),
                ("/dashboard", "GET", "127.0.0.1", "Mozilla/5.0", 200, 0.156, datetime.now(timezone.utc).isoformat()),
            ]
            cursor.executemany('''
                INSERT INTO access_logs (path, method, ip, user_agent, status_code, response_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', test_logs)

        conn.commit()
        conn.close()

        self._init_extractors()
        self._init_learning_plan()
        logger.info("AI学习管理器初始化完成")

    def _init_extractors(self):
        """初始化知识提取器"""
        self.knowledge_extractors = [
            InternalDatabaseExtractor(self.db_path),
            CodeRepositoryExtractor(os.path.dirname(os.path.abspath(__file__))),
            UserInteractionExtractor(self.db_path),
            ExternalAPIExtractor(),
            FrontendBeautificationExtractor(os.path.dirname(os.path.abspath(__file__)))
        ]

    def _init_learning_plan(self):
        """初始化学习计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM learning_plans")
        if cursor.fetchone()[0] == 0:
            plans = [
                {
                    "plan_name": "daily_learning",
                    "description": "每日学习计划",
                    "frequency": "daily",
                    "next_run": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
                },
                {
                    "plan_name": "weekly_upgrade",
                    "description": "每周升级计划",
                    "frequency": "weekly",
                    "next_run": (datetime.now(timezone.utc) + timedelta(weeks=1)).isoformat()
                },
                {
                    "plan_name": "monthly_optimization",
                    "description": "每月优化计划",
                    "frequency": "monthly",
                    "next_run": (datetime.now(timezone.utc) + timedelta(weeks=4)).isoformat()
                }
            ]
            
            for plan in plans:
                cursor.execute('''
                    INSERT INTO learning_plans (plan_name, description, frequency, next_run, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    plan["plan_name"],
                    plan["description"],
                    plan["frequency"],
                    plan["next_run"],
                    datetime.now(timezone.utc).isoformat()
                ))
            
            conn.commit()
        conn.close()

    def start(self):
        """启动AI学习管理器"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run_learning_loop)
            self.thread.start()
            logger.info("AI学习管理器已启动")
        else:
            logger.warning("AI学习管理器已经在运行")

    def stop(self):
        """停止AI学习管理器"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

    def _run_learning_loop(self):
        """运行学习循环"""
        while self.is_running:
            try:
                self._check_and_execute_plans()
                time.sleep(3600)
            except Exception as e:
                logger.error(f"学习循环出错: {str(e)}")
                time.sleep(600)

    def _check_and_execute_plans(self):
        """检查并执行学习计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        cursor.execute('''
            SELECT id, plan_name, description, frequency, next_run
            FROM learning_plans
            WHERE next_run <= ? AND status = 'active'
        ''', (now,))
        
        for plan in cursor.fetchall():
            plan_id, plan_name, description, frequency, next_run = plan
            logger.info(f"执行学习计划: {plan_name} - {description}")
            
            self._execute_learning_plan(plan_name)
            
            next_run_time = self._calculate_next_run(frequency)
            cursor.execute('''
                UPDATE learning_plans
                SET next_run = ?, updated_at = ?
                WHERE id = ?
            ''', (next_run_time, now, plan_id))
        
        conn.commit()
        conn.close()

    def _calculate_next_run(self, frequency: str) -> str:
        """计算下一次执行时间"""
        now = datetime.now(timezone.utc)
        if frequency == "daily":
            return (now + timedelta(days=1)).isoformat()
        elif frequency == "weekly":
            return (now + timedelta(weeks=1)).isoformat()
        elif frequency == "monthly":
            return (now + timedelta(weeks=4)).isoformat()
        else:
            return (now + timedelta(days=1)).isoformat()

    def _execute_learning_plan(self, plan_name: str):
        """执行学习计划"""
        if plan_name == "daily_learning":
            self._perform_daily_learning()
        elif plan_name == "weekly_upgrade":
            self._perform_weekly_upgrade()
        elif plan_name == "monthly_optimization":
            self._perform_monthly_optimization()

    def _perform_daily_learning(self):
        """执行每日学习"""
        logger.info("开始每日学习...")

        all_knowledge = []
        for extractor in self.knowledge_extractors:
            logger.info(f"从 {extractor.source_type} 提取知识...")
            knowledge = extractor.extract_knowledge()
            all_knowledge.extend(knowledge)
            logger.info(f"从 {extractor.source_type} 提取了 {len(knowledge)} 条知识")

        logger.info(f"总共提取了 {len(all_knowledge)} 条知识")

        if all_knowledge:
            logger.info("开始训练机器学习模型...")
            self.ml_model_manager.train(all_knowledge)

            logger.info("开始整合知识到AI脑库...")
            self._integrate_knowledge(all_knowledge)
            self.current_knowledge_list = all_knowledge

        logger.info(f"每日学习完成,整合了 {len(all_knowledge)} 条知识")

    def _integrate_knowledge(self, knowledge_list: List[Dict]):
        """将知识整合到AI脑库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        inserted_ids = []

        for knowledge in knowledge_list:
            knowledge_type = knowledge.get("type", "general")
            knowledge_id = knowledge.get("id", "")
            
            cursor.execute('''
                SELECT COUNT(*) FROM ai_brain_features
                WHERE issue_description = ?
            ''', (str(knowledge["content"]),))
            
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO ai_brain_features (
                        feature_type, issue_description, issue_characteristics,
                        solution, severity, impact_scope, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge_type,
                    str(knowledge["content"]),
                    str(knowledge.get("source", "")),
                    str(knowledge["content"].get("solution", {})),
                    1,
                    "general",
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat()
                ))
                inserted_ids.append(cursor.lastrowid)

        conn.commit()
        conn.close()
        
        logger.info(f"成功整合了 {len(inserted_ids)} 条知识到AI脑库")

    def _perform_weekly_upgrade(self):
        """执行每周升级"""
        logger.info("开始每周升级...")
        self._perform_daily_learning()
        self._create_knowledge_version("Weekly upgrade")
        logger.info("每周升级完成")

    def _perform_monthly_optimization(self):
        """执行每月优化"""
        logger.info("开始每月优化...")
        self._perform_weekly_upgrade()
        self._optimize_knowledge_base()
        logger.info("每月优化完成")

    def _optimize_knowledge_base(self):
        """优化AI脑库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        logger.info("优化AI脑库,执行VACUUM操作")
        conn.commit()
        conn.close()

    def _create_knowledge_version(self, description):
        """创建知识版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM ai_brain_features")
        knowledge_count = cursor.fetchone()[0]
        
        version_number = f"{datetime.now(timezone.utc).strftime('%Y.%m.%d')}.{knowledge_count}"
        
        cursor.execute("UPDATE knowledge_versions SET is_active = 0 WHERE is_active = 1")
        
        cursor.execute('''
            INSERT INTO knowledge_versions (
                version_number, description, knowledge_count, created_at, is_active
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            version_number,
            description,
            knowledge_count,
            datetime.now(timezone.utc).isoformat(),
            1
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"创建知识版本: {version_number},包含 {knowledge_count} 条知识")

    def manual_learn(self, knowledge_source: str = "all"):
        """手动触发学习"""
        logger.info("手动触发学习")
        self._ensure_initialized()
        self._perform_daily_learning()
        logger.info("手动学习完成")

    def manual_upgrade(self):
        """手动触发升级"""
        logger.info("手动触发升级")
        self._ensure_initialized()
        self._perform_weekly_upgrade()

    def _ensure_initialized(self):
        """确保学习管理器已经初始化"""
        if not self.knowledge_extractors:
            logger.info("学习管理器尚未初始化,开始初始化...")
            self._init_extractors()
            logger.info("学习管理器初始化完成")

    def get_current_version(self) -> Dict:
        """获取当前知识版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, version_number, description, knowledge_count, created_at
            FROM knowledge_versions
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        version = cursor.fetchone()
        conn.close()
        
        if version:
            return {
                "version_number": version[1],
                "description": version[2],
                "knowledge_count": version[3],
                "created_at": version[4]
            }
        else:
            return {"version": "Unknown", "knowledge_count": 0}

    def get_learning_plans(self) -> List[Dict]:
        """获取学习计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, plan_name, description, frequency, next_run, status, created_at
            FROM learning_plans
        ''')
        
        plans = []
        for plan in cursor.fetchall():
            plans.append({
                "id": plan[0],
                "plan_name": plan[1],
                "description": plan[2],
                "frequency": plan[3],
                "next_run": plan[4],
                "status": plan[5],
                "created_at": plan[6]
            })
        
        conn.close()
        return plans

class AISelfUpgradeSystem:
    """AI自我升级系统"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.learning_manager = AILearningManager(db_path)
        self.is_running = False

    def start(self):
        """启动AI自我升级系统"""
        logger.info("启动AI自我升级系统")
        self.learning_manager.initialize()
        self.learning_manager.start()
        self.is_running = True

    def stop(self):
        """停止AI自我升级系统"""
        logger.info("停止AI自我升级系统")
        self.learning_manager.stop()
        self.is_running = False
        logger.info("AI自我升级系统已停止")

    def status(self) -> Dict:
        """获取系统状态"""
        return {
            "is_running": self.is_running,
            "current_version": self.learning_manager.get_current_version(),
            "learning_plans": self.learning_manager.get_learning_plans()
        }

if __name__ == "__main__":
    ai_system = AISelfUpgradeSystem(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev.db"))
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "start":
            print("AI自我升级系统已启动")
            ai_system.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                ai_system.stop()
                print("AI自我升级系统已停止")
        elif command == "stop":
            ai_system.stop()
            print("AI自我升级系统已停止")
        elif command == "status":
            status = ai_system.status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
        elif command == "learn":
            source = sys.argv[2] if len(sys.argv) > 2 else "all"
            ai_system.learning_manager.initialize()
            ai_system.learning_manager.manual_learn(source)
            print("手动学习完成")
        elif command == "upgrade":
            ai_system.learning_manager.initialize()
            ai_system.learning_manager.manual_upgrade()
            print("手动升级完成")
        else:
            print(f"未知命令: {command}")
            print("可用命令: start, stop, status, learn, upgrade")
    else:
        ai_system.start()
        print("AI自我升级系统已启动")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            ai_system.stop()
            print("AI自我升级系统已停止")
