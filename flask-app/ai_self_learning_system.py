#!/usr/bin/env python3
"""
AI自我学习和升级系统
功能：
1. AI自身学习功能升级
2. Python技术升级AI脑库知识特征
3. 强化自升级和学习能力
4. 计划升级学习，保持AI最新最强状态
5. 机器学习模型支持，增强AI推理能力
6. 增强知识提取和整合能力
7. 改进知识图谱构建和分析
8. 自动发现和解决问题

import os
import sys
import sqlite3
# JSON import removed - using database
import logging
import traceback
import subprocess
import time
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any, Set
import threading
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_self_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 系统配置
CONFIG = {
    "db_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev.db"),
    "learning_interval_hours": 24,  # 每24小时学习一次
    "upgrade_interval_days": 7,  # 每7天升级一次
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
        self.vectorizer = TfidfVectorizer()
        self.knowledge_vectors = None
        self.knowledge_ids = None
        self.is_trained = False

    def train(self, knowledge_list: List[Dict]):
        """训练机器学习模型"""
        if not knowledge_list:
            logger.warning("没有知识数据用于训练模型")
            return False

        try:
            # 提取知识内容用于训练
            texts = []
            self.knowledge_ids = []

            for knowledge in knowledge_list:
                content = knowledge.get("content", {})
                if "problem" in content:
                    text = content["problem"]
                elif "description" in content:
                    text = content["description"]
                else:
                    text = str(content)

                texts.append(text)
                self.knowledge_ids.append(knowledge.get("id", ""))

            # 训练TF-IDF向量器
            self.knowledge_vectors = self.vectorizer.fit_transform(texts)
            self.is_trained = True
            logger.info(f"机器学习模型训练完成，使用了 {len(texts)} 条知识数据")
            return True
        except Exception as e:
            logger.error(f"训练机器学习模型出错: {str(e)}")
            return False
    def calculate_similarity(self, text: str, top_n: int = 5) -> List[Dict]:
        """计算文本与现有知识的相似度"""
        if not self.is_trained:
            logger.warning("机器学习模型尚未训练，无法计算相似度")
            return []

        try:
            # 将输入文本转换为向量
            text_vector = self.vectorizer.transform([text])

            # 计算与所有知识的相似度
            similarities = cosine_similarity(text_vector, self.knowledge_vectors)[0]

            # 获取相似度最高的top_n条知识
            top_indices = similarities.argsort()[-top_n:][::-1]

            results = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    results.append({
                        "knowledge_id": self.knowledge_ids[idx],
                        "similarity": float(similarities[idx]),
                        "rank": len(results) + 1
                    })

            return results
        except Exception as e:
            logger.error(f"计算相似度出错: {str(e)}")

    def classify_knowledge(self, knowledge: Dict) -> str:
        # 基于规则和关键词的分类
        content = knowledge.get("content", {})
        text = str(content).lower()
        # 定义分类规则
        categories = {
            "problem_solution": ["problem", "solution", "fix", "error", "bug"],
            "code_pattern": ["code", "pattern", "function", "class", "method"],
            "template_pattern": ["template", "html", "jinja", "extends", "block"],
            "css_pattern": ["css", "style", "variable", "class", "id"],
            "user_behavior": ["user", "behavior", "access", "log", "route"],
            "tech_update": ["update", "version", "feature", "framework", "library"]
        }
        # 根据关键词匹配分类
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category

        return "general"  # 默认分类

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
            # 自动分类知识
            knowledge["type"] = self.ml_model.classify_knowledge(knowledge)
            if "extracted_at" not in knowledge:
                knowledge["extracted_at"] = datetime.now(UTC).isoformat()
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
                    "source": "internal:fixes",
                    "content": {
                        "problem": error_content,
                        "solution": {
                            "strategy": eval(fix_strategy),
                            "implementation": eval(fix_implementation)
                        },
                        "timestamp": datetime.now(UTC).isoformat(),
                        "confidence": 0.9
                    }

            # 从题库表中提取知识
            cursor.execute('''
                SELECT q.content, q.answer, q.explanation, q.difficulty, c.name as category
                FROM questions q
                JOIN categories c ON q.category_id = c.id
            ''')
            for row in cursor.fetchall():
                content, answer, explanation, difficulty, category = row
                knowledge_list.append({
                    "source": "internal:questions",
                    "content": {
                        "question": content,
                        "answer": answer,
                        "explanation": explanation,
                        "difficulty": difficulty,
                        "category": category,
                        "confidence": 0.8
                    }
            conn.close()

            knowledge_list = self.preprocess_knowledge(knowledge_list)
            logger.info(f"从内部数据库提取了 {len(knowledge_list)} 条知识")
        except Exception as e:
            logger.error(f"内部数据库知识提取器出错: {str(e)}")

class CodeRepositoryExtractor(KnowledgeExtractor):
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def extract_knowledge(self) -> List[Dict]:
        """从代码仓库提取知识"""
        knowledge_list = []
        try:
            # 1. 分析Python代码，提取有用的知识
                [sys.executable, "-m", "pylint", "--output-format=json", "--enable=similarities", "app"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            if result.stdout:
                for issue in pylint_result:
                    if issue.get('type') == 'similarities':
                        knowledge_list.append({
                            "source": f"code:{issue.get('path')}:{issue.get('line')}",
                            "content": {
                                "pattern_type": "similar_code",
                                "description": issue.get('message', ''),
                                "location": f"{issue.get('path')}:{issue.get('line')}",
                                "timestamp": datetime.now(UTC).isoformat(),
                                "confidence": 0.7
                            }
                        })
            # 2. 分析HTML模板，提取结构模式
            html_files = []
            for root, dirs, files in os.walk(os.path.join(self.repo_path, "templates")):
                for file in files:
                    if file.endswith(".html"):
                        html_files.append(os.path.join(root, file))

                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 提取模板继承关系
                import re
                    knowledge_list.append({
                        "source": f"template:{os.path.basename(html_file)}",
                        "type": "template_pattern",
                        "content": {
                            "pattern_type": "template_inheritance",
                            "child_template": os.path.basename(html_file),
                            "location": html_file,
                            "timestamp": datetime.now(UTC).isoformat(),
                            "confidence": 0.8
                        }
                    })

            css_files = []
            for root, dirs, files in os.walk(os.path.join(self.repo_path, "static", "css")):
                for file in files:
                    if file.endswith(".css"):
                        css_files.append(os.path.join(root, file))

            for css_file in css_files:
                with open(css_file, 'r', encoding='utf-8') as f:

                # 提取CSS变量
                if css_vars:
                    for css_var_block in css_vars:
                        vars = re.findall(r'--([a-zA-Z0-9-]+):\s*([^;]+);', css_var_block)
                            knowledge_list.append({
                                "source": f"css:{os.path.basename(css_file)}",
                                "type": "css_pattern",
                                "content": {
                                    "pattern_type": "css_variables",
                                    "variables_count": len(vars),
                                    "variables": dict(vars),
                                    "timestamp": datetime.now(UTC).isoformat(),
                                    "confidence": 0.9
                                }

        except Exception as e:
            logger.error(f"代码仓库知识提取器出错: {str(e)}")
            traceback.print_exc()
        return knowledge_list

class FrontendBeautificationExtractor(KnowledgeExtractor):
    def __init__(self, repo_path: str):
        super().__init__("frontend_beautification")
        self.repo_path = repo_path
    def extract_knowledge(self) -> List[Dict]:
        try:
            # 检查是否存在前端美化历史文件
            if os.path.exists(beautification_history_file):
                with open(beautification_history_file, 'r', encoding='utf-8') as f:

                for record in beautification_history:
                    knowledge_list.extend(self._extract_from_beautification(record))

            # 检查是否存在前端美化知识库文件
            knowledge_base_file = os.path.join(self.repo_path, "ai_frontend_knowledge_base.json")
                with open(knowledge_base_file, 'r', encoding='utf-8') as f:
                    knowledge_base = json.load(f)
                for opt_type, optimizations in knowledge_base.items():
                    for optimization in optimizations:
                            "source": f"beautification:optimization:{opt_type}",
                            "type": "css_pattern",
                                "optimization_type": opt_type,
                                "change": optimization["change"],
                                "count": optimization["count"],
                                "last_used": optimization["last_used"]
                            }
                        })
        except Exception as e:

        return knowledge_list

    def _extract_from_beautification(self, record: Dict) -> List[Dict]:
        """从单个美化记录提取知识"""
        knowledge_list = []
        try:
            # 提取美化效果知识
            knowledge_list.append({
                "type": "code_pattern",
                "content": {
                    "file_path": record["file_path"],
                    "changes": record["changes"],
                    "original_score": record["original_score"],
                    "new_score": record["new_score"],
                    "timestamp": record["timestamp"]
                }
            })

            for change in record["changes"]:
                knowledge_list.append({
                    "source": "beautification:change",
                        "change": change,
                        "file_path": record["file_path"],
                        "file_type": os.path.splitext(record["file_path"])[1][1:],
                        "style": record["style"],
                        "timestamp": record["timestamp"]
                    }
        except Exception as e:

        return knowledge_list

    """用户交互知识提取器"""
    def __init__(self, db_path: str):
        super().__init__("user_interactions")
    def extract_knowledge(self) -> List[Dict]:
        """从用户交互中提取知识"""
        knowledge_list = []
        try:
            cursor = conn.cursor()

            # 从访问日志中提取热门路由
            cursor.execute('''
                GROUP BY path
                ORDER BY count DESC
                LIMIT 10
            ''')

            for row in cursor.fetchall():
                knowledge_list.append({
                    "source": "user:access_logs",
                    "type": "user_behavior",
                    "content": {
                        "behavior_type": "popular_route",
                        "path": path,
                        "confidence": 0.8
                    }
            logger.info(f"从用户交互中提取了 {len(knowledge_list)} 条知识")
        except Exception as e:
            logger.error(f"用户交互知识提取器出错: {str(e)}")

class ExternalAPIExtractor(KnowledgeExtractor):
    """外部API知识提取器"""
    def __init__(self):
        super().__init__("external_apis")

        """从外部API提取知识"""
        knowledge_list = []
        try:
            # 这里可以添加从外部API获取知识的逻辑
            # 例如：获取最新的技术文章、框架更新等
                "source": "external:tech_news",
                    "framework": "Flask",
                    "features": ["Improved async support", "Better error handling", "Enhanced security"],
                    "timestamp": datetime.now(UTC).isoformat(),
                    "confidence": 0.7
                }

        except Exception as e:
        return knowledge_list
    """AI学习和升级管理器"""
    def __init__(self, db_path: str):
        self.knowledge_extractors = []
        self.learning_plan = []
        self.thread = None
        self.ml_model_manager = MLModelManager()

    def initialize(self):
        """初始化学习管理器"""
        # 连接数据库并创建必要的表
        cursor = conn.cursor()

        cursor.execute('''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_number TEXT NOT NULL,
                description TEXT NOT NULL,
                knowledge_count INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 0
            )
        ''')
        # 创建学习计划表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_plans (
                plan_name TEXT NOT NULL,
                description TEXT NOT NULL,
                frequency TEXT NOT NULL,
                next_run TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                method TEXT NOT NULL,
                ip TEXT NOT NULL,
                user_agent TEXT,
                status_code INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        # 为测试添加一些访问日志数据
        cursor.execute("SELECT COUNT(*) FROM access_logs")
        if cursor.fetchone()[0] == 0:
            test_logs = [
                ("/", "GET", "127.0.0.1", "Mozilla/5.0", 200, 0.123, datetime.now(datetime.UTC).isoformat()),
                ("/login", "GET", "127.0.0.1", "Mozilla/5.0", 200, 0.098, datetime.now(datetime.UTC).isoformat()),
                ("/dashboard", "GET", "127.0.0.1", "Mozilla/5.0", 200, 0.156, datetime.now(datetime.UTC).isoformat()),
                ("/api/data", "POST", "127.0.0.1", "Mozilla/5.0", 201, 0.234, datetime.now(datetime.UTC).isoformat()),
                ("/", "GET", "192.168.1.1", "Mozilla/5.0", 200, 0.112, datetime.now(datetime.UTC).isoformat()),
                ("/login", "POST", "192.168.1.1", "Mozilla/5.0", 302, 0.189, datetime.now(datetime.UTC).isoformat()),
                ("/dashboard", "GET", "192.168.1.1", "Mozilla/5.0", 200, 0.167, datetime.now(datetime.UTC).isoformat()),
                ("/settings", "GET", "192.168.1.1", "Mozilla/5.0", 200, 0.143, datetime.now(datetime.UTC).isoformat()),
                ("/", "GET", "10.0.0.1", "Mozilla/5.0", 200, 0.134, datetime.now(datetime.UTC).isoformat()),
            ]
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', test_logs)

        conn.commit()
        conn.close()

        # 初始化知识提取器
        self._init_extractors()

        # 初始化学习计划
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

        """初始化学习计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 检查是否已有学习计划
        cursor.execute("SELECT COUNT(*) FROM learning_plans")
        if cursor.fetchone()[0] == 0:
            # 创建默认学习计划
            plans = [
                {
                    "plan_name": "daily_learning",
                    "description": "每日学习计划",
                    "frequency": "daily",
                    "next_run": (datetime.now(datetime.UTC) + timedelta(days=1)).isoformat()
                },
                {
                    "plan_name": "weekly_upgrade",
                    "description": "每周升级计划",
                    "frequency": "weekly",
                    "next_run": (datetime.now(datetime.UTC) + timedelta(weeks=1)).isoformat()
                },
                {
                    "plan_name": "monthly_optimization",
                    "description": "每月优化计划",
                    "frequency": "monthly",
                    "next_run": (datetime.now(datetime.UTC) + timedelta(weeks=4)).isoformat()
                }
            ]

                cursor.execute('''
                    INSERT INTO learning_plans (plan_name, description, frequency, next_run, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    plan["plan_name"],
                    plan["frequency"],
                    plan["next_run"],
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

    def _run_learning_loop(self):
        """运行学习循环"""
            try:
                # 检查并执行学习计划
                self._check_and_execute_plans()

                # 休眠一段时间
                time.sleep(3600)  # 每小时检查一次
            except Exception as e:
                logger.error(f"学习循环出错: {str(e)}")
                traceback.print_exc()
                time.sleep(600)  # 出错后等待10分钟再重试

    def _check_and_execute_plans(self):
        """检查并执行学习计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取当前时间
        now = datetime.now(UTC).isoformat()

        # 查询需要执行的学习计划
        cursor.execute('''
            SELECT id, plan_name, description, frequency, next_run
            FROM learning_plans
            WHERE next_run <= ? AND status = 'active'
        ''', (now,))

        for plan in cursor.fetchall():
            plan_id, plan_name, description, frequency, next_run = plan
            logger.info(f"执行学习计划: {plan_name} - {description}")

            # 执行学习计划

            # 更新下一次执行时间
            next_run_time = self._calculate_next_run(frequency)
                UPDATE learning_plans
                SET next_run = ?, updated_at = ?
                WHERE id = ?
            ''', (next_run_time, now, plan_id))

        conn.close()

    def _calculate_next_run(self, frequency: str) -> str:
        """计算下一次执行时间"""
        now = datetime.now(UTC)
        if frequency == "daily":
            return (now + timedelta(days=1)).isoformat()
        elif frequency == "weekly":
            return (now + timedelta(weeks=1)).isoformat()
        elif frequency == "monthly":
            return (now + timedelta(weeks=4)).isoformat()
            return (now + timedelta(days=1)).isoformat()

    def _execute_learning_plan(self, plan_name: str):
        """执行学习计划"""
        if plan_name == "daily_learning":
            self._perform_daily_learning()
        elif plan_name == "weekly_upgrade":
            self._perform_weekly_upgrade()
        elif plan_name == "monthly_optimization":

    def _perform_daily_learning(self):
        """执行每日学习"""
        logger.info("开始每日学习...")

        all_knowledge = []
        for extractor in self.knowledge_extractors:
            logger.info(f"从 {extractor.source_type} 提取知识...")
            knowledge = extractor.extract_knowledge()
            logger.info(f"从 {extractor.source_type} 提取了 {len(knowledge)} 条知识")

        logger.info(f"总共提取了 {len(all_knowledge)} 条知识")

        # 增强知识处理
            logger.info("开始增强知识处理...")
            all_knowledge = self._enhance_knowledge(all_knowledge)
            logger.info(f"知识增强完成，处理了 {len(all_knowledge)} 条知识")

        # 训练机器学习模型
        if all_knowledge:
            logger.info("开始训练机器学习模型...")
            self.ml_model_manager.train(all_knowledge)

        # 将知识整合到AI脑库
        if all_knowledge:
            logger.info("开始整合知识到AI脑库...")
            self._integrate_knowledge(all_knowledge)
            logger.info(f"成功整合了 {len(all_knowledge)} 条知识到AI脑库")
            self.current_knowledge_list = all_knowledge  # 更新当前知识列表
        else:
            logger.info("没有提取到任何知识，跳过整合步骤")

        logger.info(f"每日学习完成，整合了 {len(all_knowledge)} 条知识")

    def _enhance_knowledge(self, knowledge_list: List[Dict]) -> List[Dict]:
        """增强知识处理，添加额外的元数据和关联"""
        enhanced_knowledge = []

        for knowledge in knowledge_list:
            enhanced = knowledge.copy()

            # 添加知识质量评分
            quality_score = self._calculate_knowledge_quality(knowledge)
            enhanced["quality_score"] = quality_score

            # 提取关键词
            keywords = self._extract_keywords(knowledge)
            enhanced["keywords"] = keywords

            # 添加知识重要性评分
            enhanced["importance_score"] = importance_score

            enhanced_knowledge.append(enhanced)

        return enhanced_knowledge

    def _calculate_knowledge_quality(self, knowledge: Dict) -> float:
        """计算知识质量评分"""
        quality = 0.0
        content = knowledge.get("content", {})
        knowledge_type = knowledge.get("type", "")

        # 基于置信度评分
        if "confidence" in content:
            quality += content["confidence"] * 0.5

        # 基于内容完整性评分
        if "problem" in content and "solution" in content:
            quality += 0.3
        elif "description" in content and len(content["description"]) > 50:
            quality += 0.3
        # 前端美化知识的特殊处理
        elif "improvement" in content and content["improvement"] > 0:
            # 根据美化效果评分
            quality += min(content["improvement"] / 50, 0.3)  # 最多加0.3分
        elif "average_improvement" in content:
            # 根据平均改进效果评分
            quality += min(content["average_improvement"] / 50, 0.3)

        # 基于来源可靠性评分
        if source.startswith("internal"):
            quality += 0.2
        elif source.startswith("external"):
        # 前端美化知识的来源评分
        elif source.startswith("beautification"):
            quality += 0.15

        # 确保质量评分在0-1之间
        return min(1.0, max(0.0, quality))

    def _extract_keywords(self, knowledge: Dict) -> List[str]:
        """从知识中提取关键词"""
        content = knowledge.get("content", {})
        text = str(content).lower()

        # 移除标点符号
        text = re.sub(r'[^a-zA-Z0-9\s\u4e00-\u9fa5]', '', text)

        # 简单的关键词提取，基于常见技术术语和出现频率
        common_tech_terms = [
            "python", "flask", "sqlite", "ai", "机器学习", "深度学习",
            "知识图谱", "问题", "解决方案", "修复", "优化", "升级",
            "函数", "类", "方法", "模板", "css", "html", "路由", "API",
            "前端", "美化", "样式", "响应式", "动画", "过渡", "颜色", "主题",
            "布局", "设计", "用户体验", "UI", "UX", "移动端", "桌面端",
            "字体", "图标", "组件", "框架", "性能", "可访问性", "span", "div"

        for term in common_tech_terms:
            if term in text:
                keywords.append(term)

        return keywords[:5]  # 最多返回5个关键词

    def _calculate_importance(self, knowledge: Dict) -> float:
        """计算知识重要性评分"""
        importance = 0.0
        source = knowledge.get("source", "")
        knowledge_type = knowledge.get("type", "")

        # 基于知识类型评分
        if knowledge_type == "problem_solution":
            importance += 0.4
        elif knowledge_type == "code_pattern":
            importance += 0.3
        elif knowledge_type == "tech_update":
            importance += 0.3
        elif knowledge_type == "css_pattern":
            importance += 0.35  # 前端美化相关知识提高权重

        # 基于来源评分
        if source.startswith("internal:fixes"):
            importance += 0.3
        elif source.startswith("internal:questions"):
            importance += 0.2
        elif source.startswith("beautification"):
            importance += 0.25  # 前端美化知识提高来源权重

        # 基于内容评分
        # 前端美化知识的特殊内容评分
            importance += 0.15  # 改进效果显著的美化知识提高权重
        elif "average_improvement" in content and content["average_improvement"] > 5:
            importance += 0.1  # 平均改进效果好的美化知识提高权重
            importance += 0.05  # 频繁使用的美化知识提高权重

        # 确保重要性评分在0-1之间
        return min(1.0, max(0.0, importance))

    def _perform_weekly_upgrade(self):
        """执行每周升级"""
        logger.info("开始每周升级...")

        # 执行每日学习
        self._perform_daily_learning()

        # 升级AI脑库结构
        self._upgrade_knowledge_base()

        # 生成知识推荐
        self._generate_knowledge_recommendations()

        # 发现和解决问题
        self._discover_and_solve_problems()

        # 优化知识图谱
        self._optimize_knowledge_graph()

        # 生成知识版本
        self._create_knowledge_version("Weekly upgrade")

        logger.info("每周升级完成")

    def _discover_and_solve_problems(self):
        """自动发现和解决问题"""
        logger.info("开始自动发现和解决问题...")

        try:
            # 1. 检查代码库中的问题
            self._check_code_issues()

            # 2. 检查系统配置问题
            self._check_system_config()

            # 3. 检查数据库问题
            self._check_database_issues()

            logger.info("自动发现和解决问题完成")
        except Exception as e:
            logger.error(f"自动发现和解决问题出错: {str(e)}")

    def _check_code_issues(self):
        """检查代码库中的问题"""

        try:
            # 运行pylint检查代码质量
            repo_path = os.path.dirname(os.path.abspath(__file__))
            result = subprocess.run(
                [sys.executable, "-m", "pylint", "--output-format=json", "--disable=R0801", "app"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )

            if result.stdout:
                pylint_issues = eval(result.stdout)

                # 只处理严重程度较高的问题

                if critical_issues:
                    logger.info(f"发现 {len(critical_issues)} 个严重代码问题")

                    # 记录问题到AI脑库
                    for issue in critical_issues:
                        self._record_code_issue(issue)
                else:
                    logger.info("代码质量良好，未发现严重问题")
            logger.error(f"检查代码库问题出错: {str(e)}")

    def _record_code_issue(self, issue: Dict):
        """记录代码问题到AI脑库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查问题是否已存在
            cursor.execute('''
                SELECT COUNT(*) FROM ai_brain_features
                WHERE issue_description = ?
            ''', (issue.get('message', ''),))

            if cursor.fetchone()[0] == 0:
                # 插入问题到AI脑库
                cursor.execute('''
                    INSERT INTO ai_brain_features (
                        feature_type, issue_description, issue_characteristics,
                        solution, severity, impact_scope, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    "code_problem",
                    issue.get('message', ''),
                    str({
                        "line": issue.get('line', 0),
                        "module": issue.get('module', ''),
                        "object": issue.get('object', '')
                    str({"suggestion": "需要人工修复"}),
                    2,  # 严重程度: 2表示中等
                    "code",
                    datetime.now(UTC).isoformat(),
                    datetime.now(UTC).isoformat()
                ))

                logger.info(f"记录代码问题: {issue.get('message', '')}")

            conn.close()
        except Exception as e:
            logger.error(f"记录代码问题出错: {str(e)}")
    def _check_system_config(self):
        """检查系统配置问题"""

        # 检查必要的配置文件
        repo_path = os.path.dirname(os.path.abspath(__file__))
        config_files = [
            os.path.join(repo_path, ".env"),
            os.path.join(repo_path, "config.py")
        ]

            if not os.path.exists(config_file):
                logger.warning(f"缺少配置文件: {config_file}")
                # 记录配置问题到AI脑库
                self._record_config_issue(config_file, "文件不存在")
            elif os.path.getsize(config_file) == 0:
                logger.warning(f"配置文件为空: {config_file}")
                # 记录配置问题到AI脑库
                self._record_config_issue(config_file, "文件为空")

    def _record_config_issue(self, config_file: str, issue: str):
        """记录配置问题到AI脑库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查问题是否已存在
            cursor.execute('''
                WHERE issue_description = ?
            ''', (f"配置问题: {config_file} {issue}",))

                # 插入问题到AI脑库
                cursor.execute('''
                    INSERT INTO ai_brain_features (
                        feature_type, issue_description, issue_characteristics,
                        solution, severity, impact_scope, created_at, updated_at
                ''', (
                    "config_problem",
                    f"配置问题: {config_file} {issue}",
                    str({"file": config_file, "issue": issue}),
                    str({"suggestion": "需要人工修复"}),
                    1,  # 严重程度: 1表示低
                    "system",
                    datetime.now(UTC).isoformat(),
                    datetime.now(UTC).isoformat()

                conn.commit()

        except Exception as e:
            logger.error(f"记录配置问题出错: {str(e)}")

    def _check_database_issues(self):
        logger.info("检查数据库问题...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查数据库连接
            cursor.execute("SELECT 1")

            # 检查关键表是否存在
            key_tables = ["ai_brain_features", "knowledge_versions", "learning_plans"]
            for table in key_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    logger.warning(f"数据库缺少关键表: {table}")
                    # 记录数据库问题到AI脑库
                    self._record_database_issue(f"缺少关键表: {table}")

            conn.close()
        except Exception as e:
            logger.error(f"检查数据库问题出错: {str(e)}")
            # 记录数据库问题到AI脑库
            self._record_database_issue(f"连接或执行SQL出错: {str(e)}")

    def _record_database_issue(self, issue: str):
        """记录数据库问题到AI脑库"""
        try:
            cursor = conn.cursor()

            # 检查问题是否已存在
            cursor.execute('''
                SELECT COUNT(*) FROM ai_brain_features
                WHERE issue_description = ?
            ''', (f"数据库问题: {issue}",))

            if cursor.fetchone()[0] == 0:
                # 插入问题到AI脑库
                    INSERT INTO ai_brain_features (
                        feature_type, issue_description, issue_characteristics,
                        solution, severity, impact_scope, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    "database_problem",
                    str({"suggestion": "需要人工修复"}),
                    3,  # 严重程度: 3表示高
                    "database",
                    datetime.now(UTC).isoformat(),
                ))

                conn.commit()
                logger.info(f"记录数据库问题: {issue}")

            conn.close()
        except Exception as e:
            logger.error(f"记录数据库问题出错: {str(e)}")

    def _optimize_knowledge_graph(self):
        """优化知识图谱"""
        logger.info("开始优化知识图谱...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 1. 删除低置信度的关联
            cursor.execute('''
                DELETE FROM knowledge_graph WHERE confidence < 0.3
            ''')
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                logger.info(f"删除了 {deleted_count} 条低置信度的知识关联")

            # 2. 优化知识图谱查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_graph_target ON knowledge_graph(target_knowledge_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_graph_confidence ON knowledge_graph(confidence)')

            conn.commit()
            conn.close()
            logger.info("知识图谱优化完成")
        except Exception as e:

    def _perform_monthly_optimization(self):
        """执行每月优化"""

        # 执行每周升级
        self._perform_weekly_upgrade()

        # 优化AI脑库
        self._optimize_knowledge_base()

        logger.info("每月优化完成")
    def _integrate_knowledge(self, knowledge_list: List[Dict]):
        """将知识整合到AI脑库"""
        conn = sqlite3.connect(self.db_path)

        inserted_ids = []

        for knowledge in knowledge_list:
            # 获取知识类型，提供默认值
            knowledge_type = knowledge.get("type", "general")

            # 检查知识是否已存在
                SELECT COUNT(*) FROM ai_brain_features
                WHERE issue_description = ?
                # 插入新知识
                cursor.execute('''
                    INSERT INTO ai_brain_features (
                        feature_type, issue_description, issue_characteristics,
                        solution, severity, impact_scope, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge_type,
                    str(knowledge["content"]),
                    str(knowledge["content"].get("solution", {})),
                    "general",  # 默认影响范围
                    datetime.now(UTC).isoformat()
                inserted_ids.append(cursor.lastrowid)

        conn.commit()

        # 构建知识图谱，建立知识之间的关联
            self._build_knowledge_graph(inserted_ids)
        logger.info(f"成功整合了 {len(inserted_ids)} 条知识到AI脑库")
        """构建知识图谱，建立知识之间的关联"""
        cursor = conn.cursor()

        logger.info(f"开始构建知识图谱，处理 {len(knowledge_ids)} 条新知识...")

        # 获取所有知识
            FROM ai_brain_features
        ''')
        all_knowledge = cursor.fetchall()

        for new_id in knowledge_ids:
            # 获取新知识
            cursor.execute('''
                SELECT feature_type, issue_description, issue_characteristics
                FROM ai_brain_features
                WHERE id = ?
            ''', (new_id,))
            new_knowledge = cursor.fetchone()
            if not new_knowledge:
                continue

            new_type, new_desc, new_chars = new_knowledge

            # 与现有知识建立关联
            for knowledge in all_knowledge:
                existing_id, existing_type, existing_desc, existing_chars = knowledge
                if new_id == existing_id:
                    continue

                # 基于知识类型和内容计算相似度

                # 类型相同，相似度增加
                if new_type == existing_type:

                # 内容有重叠，相似度增加
                if new_desc in existing_desc or existing_desc in new_desc:
                    similarity += 0.3

                # 如果相似度足够高，建立关联
                    # 检查关联是否已存在
                    cursor.execute('''
                        SELECT COUNT(*) FROM knowledge_graph
                    ''', (new_id, existing_id))

                        now = datetime.now(UTC).isoformat()
                        cursor.execute('''
                                source_knowledge_id, target_knowledge_id, relationship_type,
                                confidence, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            new_id,
                            "related",
                            similarity,
                            now,
                        ))

        conn.close()


    def _generate_knowledge_recommendations(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()


        # 获取所有知识
        cursor.execute('SELECT id FROM ai_brain_features')

        for knowledge_id in knowledge_ids:
            # 基于知识图谱获取相关知识
            cursor.execute('''
                SELECT target_knowledge_id, confidence
                WHERE source_knowledge_id = ?
                LIMIT 5
            ''', (knowledge_id,))

            related_knowledge = cursor.fetchall()

            for related_id, confidence in related_knowledge:
                # 检查推荐是否已存在
                cursor.execute('''
                    SELECT COUNT(*) FROM knowledge_recommendations
                    WHERE knowledge_id = ? AND recommended_knowledge_id = ?
                ''', (knowledge_id, related_id))

                if cursor.fetchone()[0] == 0:
                    # 生成推荐
                    now = datetime.now(UTC).isoformat()
                    cursor.execute('''
                        INSERT INTO knowledge_recommendations (
                            knowledge_id, recommended_knowledge_id, recommendation_score,
                            recommendation_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        knowledge_id,
                        related_id,
                        confidence,
                        "knowledge_graph",
                        now,
                        now
                    ))

        conn.commit()

        logger.info("知识推荐生成完成")

    def _upgrade_knowledge_base(self):
        """升级AI脑库结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. 添加知识图谱表，用于构建知识之间的关联
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_knowledge_id INTEGER NOT NULL,
                target_knowledge_id INTEGER NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (target_knowledge_id) REFERENCES ai_brain_features(id)
            )
        ''')

        # 2. 添加知识推荐表，用于存储推荐的知识关联
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommended_knowledge_id INTEGER NOT NULL,
                recommendation_score REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (knowledge_id) REFERENCES ai_brain_features(id),
                FOREIGN KEY (recommended_knowledge_id) REFERENCES ai_brain_features(id)
        ''')

        # 3. 为现有表添加索引，提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_brain_features_severity ON ai_brain_features(severity)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_brain_features_impact ON ai_brain_features(impact_scope)')
        logger.info("升级AI脑库结构完成")
        conn.commit()

    def _optimize_knowledge_base(self):
        """优化AI脑库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 优化数据库
        cursor.execute("VACUUM")
        logger.info("优化AI脑库，执行VACUUM操作")

        conn.commit()

        """创建知识版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取当前知识数量
        cursor.execute("SELECT COUNT(*) FROM ai_brain_features")
        knowledge_count = cursor.fetchone()[0]

        # 生成版本号
        version_number = f"{datetime.now(UTC).strftime('%Y.%m.%d')}.{knowledge_count}"

        # 关闭当前活动版本
        cursor.execute("UPDATE knowledge_versions SET is_active = 0 WHERE is_active = 1")

        # 创建新版本
        cursor.execute('''
            INSERT INTO knowledge_versions (
                version_number, description, knowledge_count, created_at, is_active
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            version_number,
            description,
            knowledge_count,
        ))

        conn.commit()
        conn.close()

        logger.info(f"创建知识版本: {version_number}，包含 {knowledge_count} 条知识")

    def manual_learn(self, knowledge_source: str = "all"):
        """手动触发学习"""

        # 确保学习管理器已经初始化
        self._ensure_initialized()
        # 执行每日学习

        logger.info("手动学习完成")

    def manual_upgrade(self):
        """手动触发升级"""
        logger.info("手动触发升级")

        # 确保学习管理器已经初始化
        self._ensure_initialized()

        # 执行每周升级
        self._perform_weekly_upgrade()


    def _ensure_initialized(self):
        """确保学习管理器已经初始化"""
        if not self.knowledge_extractors:
            logger.info("学习管理器尚未初始化，开始初始化...")
            self._init_extractors()
            logger.info("学习管理器初始化完成")

    def get_current_version(self) -> Dict:
        """获取当前知识版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
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
            }
        else:
            return {"version": "Unknown", "knowledge_count": 0}

    def get_learning_plans(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, plan_name, description, frequency, next_run, status, created_at
        ''')

        for plan in cursor.fetchall():
            plans.append({
                "id": plan[0],
                "plan_name": plan[1],
                "description": plan[2],
                "frequency": plan[3],
                "next_run": plan[4],
                "created_at": plan[6]
            })
        conn.close()
        return plans

class AISelfUpgradeSystem:
    """AI自我升级系统"""
        self.db_path = db_path
        self.learning_manager = AILearningManager(db_path)
        self.is_running = False

    def start(self):
        logger.info("启动AI自我升级系统")

        # 初始化学习管理器
        self.learning_manager.initialize()

        # 启动学习循环
        self.learning_manager.start()

        self.is_running = True

    def stop(self):
        """停止AI自我升级系统"""
        logger.info("停止AI自我升级系统")

        # 停止学习循环
        self.learning_manager.stop()

        self.is_running = False
        logger.info("AI自我升级系统已停止")

    def status(self) -> Dict:
        return {
            "current_version": self.learning_manager.get_current_version(),
            "learning_plans": self.learning_manager.get_learning_plans()
        }

# 主函数
if __name__ == "__main__":
    ai_system = AISelfUpgradeSystem(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev.db"))
    # 解析命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "start":
            print("AI自我升级系统已启动")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                ai_system.stop()
                print("AI自我升级系统已停止")
        elif command == "stop":
            ai_system.stop()
            print("AI自我升级系统已停止")
        elif command == "status":
        elif command == "learn":
            source = sys.argv[2] if len(sys.argv) > 2 else "all"
            ai_system.learning_manager.manual_learn(source)
            print("手动学习完成")
        elif command == "upgrade":
            ai_system.learning_manager.manual_upgrade()
            print("手动升级完成")
        else:
            print(f"未知命令: {command}")
            print("可用命令: start, stop, status, learn, upgrade")
    else:
        # 默认启动系统
        ai_system.start()
        print("AI自我升级系统已启动")
        # 保持程序运行
        try:
            while True:
            ai_system.stop()
            print("AI自我升级系统已停止")
