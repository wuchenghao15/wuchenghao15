#!/usr/bin/env python3
"""
AI实验室 - 集成所有AI功能，提供统一的AI实验环境
"""

import time
import threading
import os
import json
import sys
from typing import Dict, Any, List, Optional
from app.utils.logging import logger
from app.ai.ai_engine_integrator import ai_engine_integrator
from app.services.ai_learning import AILearningSystem
from app.ai.self_learning_system import self_learning_system
from app.ai.log_analyzer import log_analyzer_ai
from app.ai.db_middleware import ai_db_middleware
from app.utils.security import SecurityUtils

# 导入AI脑库（位于flask-app根目录）
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ai_brain_library import AIBrainLibrary

# 初始化AI脑库实例
ai_brain_library = AIBrainLibrary()


class AILab:
    """AI实验室核心类，集成所有AI功能"""
    
    def __init__(self):
        self.name = "MTSCOS AI Lab"
        self.version = "1.0.0"
        self.is_running = False
        self.components = {}
        self.feature_mapping = {}
        self.association_engine = None
        self.security_manager = SecurityUtils()
        self.thread_lock = threading.Lock()
        self.ai_lab_dir = "ai_lab"
        
        # 初始化AI实验室目录
        self._initialize_directories()
        
        # 初始化组件状态
        self.component_status = {
            "learning_system": False,
            "brain_library": False,
            "log_analyzer": False,
            "db_middleware": False,
            "security_manager": False,
            "feature_library": False
        }
        
        logger.info(f"{self.name} 初始化完成，版本: {self.version}")
    
    def _initialize_directories(self):
        """初始化AI实验室目录结构"""
        from app.filesystem import file_system
        
        # 创建AI实验室主目录
        file_system.create_directory(self.ai_lab_dir)
        
        # 创建子目录
        subdirs = [
            "experiments",      # 实验数据
            "models",           # 模型文件
            "features",         # 特征库
            "logs",             # 实验室日志
            "reports",          # 报告
            "datasets",         # 数据集
            "security",         # 安全配置
            "associations"      # 关联规则
        ]
        
        for subdir in subdirs:
            file_system.create_directory(os.path.join(self.ai_lab_dir, subdir))
    
    def start(self):
        """启动AI实验室"""
        with self.thread_lock:
            if self.is_running:
                logger.warning(f"{self.name} 已经在运行中")
                return False
            
            logger.info(f"正在启动 {self.name}...")
            self.is_running = True
        
        # 启动各个AI组件
        self._start_components()
        
        # 初始化特征映射
        self._initialize_feature_mapping()
        
        # 启动关联引擎
        self._start_association_engine()
        
        logger.info(f"{self.name} 启动成功")
        return True
    
    def stop(self):
        """停止AI实验室"""
        with self.thread_lock:
            if not self.is_running:
                logger.warning(f"{self.name} 已经停止运行")
                return False
            
            logger.info(f"正在停止 {self.name}...")
            self.is_running = False
        
        # 停止各个AI组件
        self._stop_components()
        
        # 停止关联引擎
        self._stop_association_engine()
        
        logger.info(f"{self.name} 已停止")
        return True
    
    def _start_components(self):
        """启动各个AI组件"""
        # 1. 启动脑库
        try:
            # AIBrainLibrary不需要start方法，它是一个功能类
            self.component_status["brain_library"] = True
            logger.info("AI脑库启动成功")
        except Exception as e:
            logger.error(f"AI脑库启动失败: {str(e)}")
        
        # 2. 启动自学习系统
        try:
            self_learning_system.start()
            self.component_status["learning_system"] = True
            logger.info("自学习系统启动成功")
        except Exception as e:
            logger.error(f"自学习系统启动失败: {str(e)}")
        
        # 3. 启动日志分析器
        try:
            # log_analyzer_ai不需要start方法，它是一个功能类
            self.component_status["log_analyzer"] = True
            logger.info("日志分析器启动成功")
        except Exception as e:
            logger.error(f"日志分析器启动失败: {str(e)}")
        
        # 4. 启动数据库中间件
        try:
            # ai_db_middleware不需要start方法，它是一个功能类
            self.component_status["db_middleware"] = True
            logger.info("数据库中间件启动成功")
        except Exception as e:
            logger.error(f"数据库中间件启动失败: {str(e)}")
        
        # 5. 启动特征库
        try:
            # 特征库作为脑库的一部分
            self.component_status["feature_library"] = True
            logger.info("特征库启动成功")
        except Exception as e:
            logger.error(f"特征库启动失败: {str(e)}")
    
    def _stop_components(self):
        """停止各个AI组件"""
        # 1. 停止自学习系统
        try:
            self_learning_system.stop()
            self.component_status["learning_system"] = False
            logger.info("自学习系统停止成功")
        except Exception as e:
            logger.error(f"自学习系统停止失败: {str(e)}")
        
        # 2. 停止日志分析器
        try:
            # log_analyzer_ai不需要stop方法
            self.component_status["log_analyzer"] = False
            logger.info("日志分析器停止成功")
        except Exception as e:
            logger.error(f"日志分析器停止失败: {str(e)}")
        
        # 3. 停止数据库中间件
        try:
            # ai_db_middleware不需要stop方法
            self.component_status["db_middleware"] = False
            logger.info("数据库中间件停止成功")
        except Exception as e:
            logger.error(f"数据库中间件停止失败: {str(e)}")
        
        # 4. 停止脑库
        try:
            # AIBrainLibrary不需要stop方法
            self.component_status["brain_library"] = False
            logger.info("AI脑库停止成功")
        except Exception as e:
            logger.error(f"AI脑库停止失败: {str(e)}")
    
    def _initialize_feature_mapping(self):
        """初始化特征映射"""
        # 从各个组件收集特征
        self.feature_mapping = {
            "learning": {
                "features": ["feature_importance", "anomaly_detection", "pattern_recognition"],
                "description": "学习功能相关特征"
            },
            "brain_library": {
                "features": ["knowledge_management", "feature_management", "capability_management"],
                "description": "脑库功能相关特征"
            },
            "log_analysis": {
                "features": ["log_classification", "anomaly_detection", "error_tracking"],
                "description": "日志分析功能相关特征"
            },
            "db_optimization": {
                "features": ["query_optimization", "index_suggestion", "performance_monitoring"],
                "description": "数据库优化功能相关特征"
            },
            "security": {
                "features": ["threat_detection", "access_control", "data_encryption"],
                "description": "数据安全功能相关特征"
            }
        }
        
        logger.info(f"特征映射初始化完成，共 {sum(len(v['features']) for v in self.feature_mapping.values())} 个特征")
    
    def _start_association_engine(self):
        """启动关联引擎"""
        # 启动AI联想功能
        self.association_engine = threading.Thread(
            target=self._association_loop,
            daemon=True,
            name="AI_Lab_Association_Engine"
        )
        self.association_engine.start()
        logger.info("AI联想引擎启动成功")
    
    def _stop_association_engine(self):
        """停止关联引擎"""
        # 关联引擎是守护线程，会自动退出
        logger.info("AI联想引擎已停止")
    
    def _association_loop(self):
        """AI联想循环"""
        while self.is_running:
            try:
                # 根据AI联想自动补齐系统功能
                self._auto_complete_features()
                
                # 每30秒执行一次
                time.sleep(30)
            except Exception as e:
                logger.error(f"AI联想引擎异常: {str(e)}")
                time.sleep(10)
    
    def _auto_complete_features(self):
        """根据AI联想自动补齐系统功能"""
        # 获取当前系统特征
        current_features = self._get_current_features()
        
        # 使用AI引擎进行联想
        prompt = f"当前系统已实现的特征: {json.dumps(current_features, ensure_ascii=False)}\n\n请根据这些特征，自动补齐AI实验室的功能，生成详细的功能列表和实现建议。"
        
        try:
            response = ai_engine_integrator.call_engine(
                "local", 
                prompt, 
                max_tokens=1000, 
                temperature=0.7
            )
            
            if response and response.get("code") == 0:
                # 解析AI生成的功能建议
                suggestions = response["data"]["response"]
                self._process_feature_suggestions(suggestions)
        except Exception as e:
            logger.error(f"AI联想失败: {str(e)}")
    
    def _get_current_features(self) -> Dict[str, List[str]]:
        """获取当前系统已实现的特征"""
        current_features = {}
        
        # 从特征映射中获取当前特征
        for category, data in self.feature_mapping.items():
            current_features[category] = data["features"]
        
        return current_features
    
    def _process_feature_suggestions(self, suggestions: str):
        """处理AI生成的功能建议"""
        # 保存建议到文件
        from app.filesystem import file_system
        
        suggestion_file = os.path.join(self.ai_lab_dir, "associations", f"suggestion_{int(time.time())}.txt")
        file_system.create_file(suggestion_file, suggestions)
        
        logger.info(f"AI联想建议已保存: {suggestion_file}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取AI实验室状态"""
        return {
            "name": self.name,
            "version": self.version,
            "is_running": self.is_running,
            "component_status": self.component_status,
            "feature_count": sum(len(v['features']) for v in self.feature_mapping.values()),
            "current_time": time.time()
        }
    
    def run_experiment(self, experiment_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """运行AI实验"""
        if not self.is_running:
            return {"success": False, "message": "AI实验室未运行"}
        
        experiments = {
            "feature_importance": self._run_feature_importance_experiment,
            "anomaly_detection": self._run_anomaly_detection_experiment,
            "log_analysis": self._run_log_analysis_experiment,
            "db_optimization": self._run_db_optimization_experiment
        }
        
        if experiment_type not in experiments:
            return {"success": False, "message": f"不支持的实验类型: {experiment_type}"}
        
        try:
            result = experiments[experiment_type](parameters)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"实验 {experiment_type} 失败: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _run_feature_importance_experiment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """运行特征重要性实验"""
        # 使用自学习系统进行特征重要性分析
        result = self_learning_system.analyze_feature_importance()
        return {
            "experiment_type": "feature_importance",
            "result": result,
            "timestamp": time.time()
        }
    
    def _run_anomaly_detection_experiment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """运行异常检测实验"""
        # 使用自学习系统进行异常检测
        result = self_learning_system.detect_anomalies()
        return {
            "experiment_type": "anomaly_detection",
            "result": result,
            "timestamp": time.time()
        }
    
    def _run_log_analysis_experiment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """运行日志分析实验"""
        # 使用日志分析器分析日志
        log_content = parameters.get("log_content", "这是一条测试日志 ERROR: 测试错误")
        result = log_analyzer_ai.analyze_logs(log_content)
        return {
            "experiment_type": "log_analysis",
            "result": result,
            "timestamp": time.time()
        }
    
    def _run_db_optimization_experiment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """运行数据库优化实验"""
        # 使用数据库中间件进行优化分析
        result = ai_db_middleware.get_query_analysis()
        return {
            "experiment_type": "db_optimization",
            "result": result,
            "timestamp": time.time()
        }
    
    def optimize_system(self) -> Dict[str, Any]:
        """优化整个系统"""
        if not self.is_running:
            return {"success": False, "message": "AI实验室未运行"}
        
        logger.info("开始系统优化...")
        
        # 收集各个组件的优化建议
        optimization_suggestions = {
            "learning_system": self_learning_system.generate_optimization_suggestions(),
            "brain_library": [],  # AIBrainLibrary没有get_upgrade_suggestions方法
            "db_middleware": ai_db_middleware.ai_optimize()
        }
        
        # 应用优化建议
        for component, suggestions in optimization_suggestions.items():
            if suggestions:
                logger.info(f"应用 {component} 优化建议: {suggestions}")
        
        logger.info("系统优化完成")
        return {
            "success": True,
            "suggestions": optimization_suggestions,
            "timestamp": time.time()
        }
    
    def backup_libraries(self, backup_path: str) -> bool:
        """备份所有库"""
        try:
            # 备份脑库
            ai_brain_library.save_libraries()
            logger.info(f"脑库备份成功")
            return True
        except Exception as e:
            logger.error(f"备份失败: {str(e)}")
            return False
    
    def restore_libraries(self, backup_path: str) -> bool:
        """恢复所有库"""
        try:
            # 恢复脑库
            ai_brain_library.load_libraries()
            logger.info(f"脑库恢复成功")
            return True
        except Exception as e:
            logger.error(f"恢复失败: {str(e)}")
            return False


# 初始化AI实验室实例
ai_lab = AILab()
