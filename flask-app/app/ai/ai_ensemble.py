import time
import threading
import os
import sys
from app.utils.logging import logger
from app.ai.instances import ai_instance_manager
from app.ai.monitoring import ai_monitor
try:
    from app.ai.learning import ai_learning
except ImportError:
    # 创建简单的替代实现
    class SimpleAI:
        def __init__(self):
            self.model_path = 'models/'
        
        def learn(self, data):
            return {}
        
        def process(self, data):
            return {}
    
    ai_learning = SimpleAI()
try:
    from app.ai.route_optimizer import route_optimizer
except ImportError:
    # 创建简单的替代实现
    class SimpleRouteOptimizer:
        def __init__(self):
            self.model_path = 'models/'
        
        def process(self, data):
            return {}
        
        def learn(self, data):
            return {}
    
    route_optimizer = SimpleRouteOptimizer()
try:
    from app.ai.question_generator import ai_question_generator
except ImportError:
    # 创建简单的替代实现
    class SimpleAiQuestionGenerator:
        def __init__(self):
            self.model_path = 'models/'
        
        def process(self, data):
            return {}
        
        def learn(self, data):
            return {}
    
    ai_question_generator = SimpleAiQuestionGenerator()
try:
    from app.ai.sandbox_manager import sandbox_manager
except ImportError:
    # 创建简单的替代实现
    class SimpleSandboxManager:
        def __init__(self):
            self.model_path = 'models/'
        
        def process(self, data):
            return {}
        
        def learn(self, data):
            return {}
    
    sandbox_manager = SimpleSandboxManager()
try:
    from app.ai.code_analyzer import ai_code_analyzer
except ImportError:
    # 创建简单的替代实现
    class SimpleAiCodeAnalyzer:
        def __init__(self):
            self.model_path = 'models/'
        
        def process(self, data):
            return {}
        
        def learn(self, data):
            return {}
    
    ai_code_analyzer = SimpleAiCodeAnalyzer()
try:
    from app.ai.auth import auth_ai
except ImportError:
    # 创建简单的替代实现
    class SimpleAuthAi:
        def __init__(self):
            self.model_path = 'models/'
        
        def process(self, data):
            return {}
        
        def learn(self, data):
            return {}
    
    auth_ai = SimpleAuthAi()
try:
    from app.ai.validator import validator_ai
except ImportError:
    # 创建简单的替代实现
    class SimpleValidatorAi:
        def __init__(self):
            self.model_path = 'models/'
        
        def process(self, data):
            return {}
        
        def learn(self, data):
            return {}
    
    validator_ai = SimpleValidatorAi()
try:
    from app.ai.log_analyzer import log_analyzer_ai
except ImportError:
    # 创建简单的替代实现
    class SimpleLogAnalyzerAi:
        def __init__(self):
            self.model_path = 'models/'
        
        def process(self, data):
            return {}
        
        def learn(self, data):
            return {}
    
    log_analyzer_ai = SimpleLogAnalyzerAi()
try:
    from app.ai.cleanup import cleanup_ai
except ImportError:
    # 创建简单的替代实现
    class SimpleCleanupAi:
        def __init__(self):
            self.model_path = 'models/'
        
        def process(self, data):
            return {}
        
        def learn(self, data):
            return {}
    
    cleanup_ai = SimpleCleanupAi()
from app.ai.theme import theme_ai
from app.ai.registration import registration_ai
from app.ai.login import login_ai
from app.ai.question_bank_expander import ai_question_bank_expander
from app.ai.animation_fixer import animation_fixer_ai
from app.ai.version_manager import version_manager_ai
from app.ai.backup_manager import backup_manager_ai
from app.ai.rule_manager import rule_manager_ai
from app.ai.ai_engine_integrator import ai_engine_integrator

class AIEnsemble:
    """AI集管理器，用于统一调配所有专用子AI，实现自我学习优化和项目适配"""
    
    def __init__(self):
        self.ensemble_id = "main_ai_ensemble"
        self.name = "主AI集"
        self.description = "统一管理和调配所有专用子AI的集合，实现自我学习优化和项目适配"
        self.status = "active"
        self.created_at = time.time()
        self.updated_at = time.time()
        self.sub_ais = {}
        self.lock = threading.Lock()
        self.task_history = []  # 任务历史记录，用于学习优化
        self.project_features = self._detect_project_features()  # 自动检测项目功能
        self.required_ai_types = self._determine_required_ai_types()  # 根据项目功能确定需要的AI类型
        
        # 初始化主AI集
        self._init_ensemble()
        
        # 智能实例化子AI
        self._smart_init_sub_ais()
        
        logger.info("AI集初始化完成，已智能实例化所需子AI")
        logger.info(f"项目功能: {self.project_features}")
        logger.info(f"所需AI类型: {self.required_ai_types}")
    
    def _detect_project_features(self):
        """自动检测项目功能"""
        features = []
        
        # 检测项目目录结构和关键文件
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        # 检测认证相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'auth.py')) or os.path.exists(os.path.join(project_root, 'app', 'models', 'user.py')):
            features.append('authentication')
        
        # 检测测试相关功能
        test_files = [
            os.path.join(project_root, 'app', 'models', 'question.py'),
            os.path.join(project_root, 'app', 'models', 'test_result.py')
        ]
        if any(os.path.exists(f) for f in test_files):
            features.append('testing')
        
        # 检测题库扩充相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'ai', 'question_bank_expander.py')):
            features.append('question_bank_expansion')
        
        # 检测学习相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'ai', 'learning.py')):
            features.append('learning')
        
        # 检测监控相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'ai', 'monitoring.py')):
            features.append('monitoring')
        
        # 检测代码分析相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'ai', 'code_analyzer.py')):
            features.append('code_analysis')
        
        # 检测主题相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'ai', 'theme.py')):
            features.append('theme_management')
        
        # 检测注册和登录功能
        if os.path.exists(os.path.join(project_root, 'app', 'ai', 'registration.py')) or os.path.exists(os.path.join(project_root, 'app', 'ai', 'login.py')):
            features.append('user_management')
        
        # 检测动画修复相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'ai', 'animation_fixer.py')):
            features.append('animation_fix')
        
        # 检测版本管理相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'ai', 'version_manager.py')):
            features.append('version_management')
        
        # 检测备份管理相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'models', 'backup.py')):
            features.append('backup_management')
        
        # 检测规则管理相关功能
        if os.path.exists(os.path.join(project_root, 'app', 'ai', 'rule_manager.py')):
            features.append('rule_management')
        
        logger.info(f"自动检测到的项目功能: {features}")
        return features
    
    def _determine_required_ai_types(self):
        """根据项目功能确定需要的AI类型"""
        required_ai_types = set()
        
        # 功能到AI类型的映射
        feature_to_ai_map = {
            'authentication': ['auth', 'validator'],
            'testing': ['question_generator', 'test_generator', 'test_supervisor'],
            'learning': ['learning'],
            'monitoring': ['monitoring', 'log_analyzer'],
            'code_analysis': ['code_analyzer'],
            'theme_management': ['theme'],
            'user_management': ['registration', 'login'],
            'question_bank_expansion': ['question_bank_expander'],
            'animation_fix': ['animation_fixer'],
            'version_management': ['version_manager'],
            'backup_management': ['backup_manager'],
            'rule_management': ['rule_manager']
        }
        
        # 基础AI类型，所有项目都需要
        base_ai_types = ['cleanup', 'sandbox_manager', 'route_optimizer']
        for ai_type in base_ai_types:
            required_ai_types.add(ai_type)
        
        # 根据检测到的功能添加所需AI类型
        for feature in self.project_features:
            if feature in feature_to_ai_map:
                for ai_type in feature_to_ai_map[feature]:
                    required_ai_types.add(ai_type)
        
        return list(required_ai_types)
    
    def _init_ensemble(self):
        """初始化主AI集"""
        # 检查AI集是否已存在
        existing_collection = ai_instance_manager.get_collection(self.ensemble_id)
        if not existing_collection:
            # 创建AI集
            ai_instance_manager.create_collection(
                collection_id=self.ensemble_id,
                name=self.name,
                description=self.description,
                status=self.status
            )
            logger.info(f"创建主AI集成功: {self.ensemble_id}")
        else:
            logger.info(f"主AI集已存在: {self.ensemble_id}")
    
    def _smart_init_sub_ais(self):
        """智能实例化所需子AI"""
        with self.lock:
            # AI类型到初始化方法的映射
            init_methods = {
                'monitoring': self._init_monitoring_ai,
                'learning': self._init_learning_ai,
                'route_optimizer': self._init_route_optimizer_ai,
                'question_generator': self._init_question_generator_ai,
                'test_generator': self._init_test_generator_ai,
                'sandbox_manager': self._init_sandbox_manager_ai,
                'code_analyzer': self._init_code_analyzer_ai,
                'test_supervisor': self._init_test_supervisor_ai,
                'auth': self._init_auth_ai,
                'validator': self._init_validator_ai,
                'log_analyzer': self._init_log_analyzer_ai,
                'cleanup': self._init_cleanup_ai,
                'theme': self._init_theme_ai,
                'registration': self._init_registration_ai,
                'login': self._init_login_ai,
                'question_bank_expander': self._init_question_bank_expander_ai,
                'animation_fixer': self._init_animation_fixer_ai,
                'version_manager': self._init_version_manager_ai,
                'backup_manager': self._init_backup_manager_ai,
                'rule_manager': self._init_rule_manager_ai
            }
            
            # 只实例化所需的AI类型
            for ai_type in self.required_ai_types:
                if ai_type in init_methods:
                    try:
                        init_methods[ai_type]()
                    except Exception as e:
                        logger.error(f"实例化 {ai_type} AI失败: {str(e)}")
                else:
                    logger.warning(f"未找到 {ai_type} AI的初始化方法")
    
    def _init_monitoring_ai(self):
        """实例化监控AI"""
        instance_id = "monitoring_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="monitoring",
            name="监控AI",
            description="负责系统监控、错误检测和性能分析",
            functions=["monitor_system", "detect_errors", "analyze_performance"],
            responsibilities=["系统监控", "错误检测", "性能分析"],
            config={"monitoring_enabled": True, "error_threshold": 5},
            collection_id=self.ensemble_id
        )
        self.sub_ais["monitoring"] = instance_id
        logger.info("监控AI实例化成功")
    
    def _init_learning_ai(self):
        """实例化学习AI"""
        instance_id = "learning_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="learning",
            name="学习AI",
            description="负责AI自主学习和模型优化",
            functions=["self_learning", "model_optimization", "knowledge_acquisition"],
            responsibilities=["自主学习", "模型优化", "知识获取"],
            config={"learning_enabled": True, "optimization_interval": 3600},
            collection_id=self.ensemble_id
        )
        self.sub_ais["learning"] = instance_id
        logger.info("学习AI实例化成功")
    
    def _init_route_optimizer_ai(self):
        """实例化路由优化AI"""
        instance_id = "route_optimizer_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="route_optimizer",
            name="路由优化AI",
            description="负责系统路由优化和负载均衡",
            functions=["optimize_routes", "load_balancing", "performance_monitoring"],
            responsibilities=["路由优化", "负载均衡", "性能监控"],
            config={"optimization_enabled": True, "check_interval": 600},
            collection_id=self.ensemble_id
        )
        self.sub_ais["route_optimizer"] = instance_id
        logger.info("路由优化AI实例化成功")
    
    def _init_question_generator_ai(self):
        """实例化问题生成AI"""
        instance_id = "question_generator_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="question_generator",
            name="问题生成AI",
            description="负责生成各种类型的测试问题",
            functions=["generate_questions", "validate_questions", "optimize_questions"],
            responsibilities=["问题生成", "问题验证", "问题优化"],
            config={"auto_generate": True, "language_support": ["japanese", "english"]},
            collection_id=self.ensemble_id
        )
        self.sub_ais["question_generator"] = instance_id
        logger.info("问题生成AI实例化成功")
    
    def _init_test_generator_ai(self):
        """实例化测试生成AI"""
        instance_id = "test_generator_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="test_generator",
            name="测试生成AI",
            description="负责生成完整的测试试卷",
            functions=["generate_test_paper", "evaluate_test", "analyze_results"],
            responsibilities=["测试生成", "测试评估", "结果分析"],
            config={"supported_languages": ["japanese", "english"], "test_types": ["practice", "level"]},
            collection_id=self.ensemble_id
        )
        self.sub_ais["test_generator"] = instance_id
        logger.info("测试生成AI实例化成功")
    
    def _init_sandbox_manager_ai(self):
        """实例化沙盒管理AI"""
        instance_id = "sandbox_manager_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="sandbox_manager",
            name="沙盒管理AI",
            description="负责管理AI沙盒环境",
            functions=["create_sandbox", "destroy_sandbox", "monitor_sandbox"],
            responsibilities=["沙盒创建", "沙盒销毁", "沙盒监控"],
            config={"sandbox_enabled": True, "dynamic_sandbox": {"enabled": True}},
            collection_id=self.ensemble_id
        )
        self.sub_ais["sandbox_manager"] = instance_id
        logger.info("沙盒管理AI实例化成功")
    
    def _init_code_analyzer_ai(self):
        """实例化代码分析AI"""
        instance_id = "code_analyzer_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="code_analyzer",
            name="代码分析AI",
            description="负责代码分析和优化建议",
            functions=["analyze_code", "generate_suggestions", "optimize_code"],
            responsibilities=["代码分析", "优化建议", "代码优化"],
            config={"analysis_enabled": True, "auto_fix": False},
            collection_id=self.ensemble_id
        )
        self.sub_ais["code_analyzer"] = instance_id
        logger.info("代码分析AI实例化成功")
    
    def _init_test_supervisor_ai(self):
        """实例化测试监管AI"""
        instance_id = "test_supervisor_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="test_supervisor",
            name="测试监管AI",
            description="负责监管测试过程和结果",
            functions=["supervise_test", "validate_result", "generate_report"],
            responsibilities=["测试监管", "结果验证", "报告生成"],
            config={"supervision_enabled": True, "report_format": "json"},
            collection_id=self.ensemble_id
        )
        self.sub_ais["test_supervisor"] = instance_id
        logger.info("测试监管AI实例化成功")
    
    def _init_auth_ai(self):
        """实例化用户认证AI"""
        instance_id = "auth_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="auth",
            name="用户认证AI",
            description="负责用户认证和权限管理",
            functions=["authenticate_user", "verify_permission", "manage_session"],
            responsibilities=["用户认证", "权限验证", "会话管理"],
            config={"auth_enabled": True, "session_timeout": 1800},
            collection_id=self.ensemble_id
        )
        self.sub_ais["auth"] = instance_id
        logger.info("用户认证AI实例化成功")
    
    def _init_validator_ai(self):
        """实例化数据验证AI"""
        instance_id = "validator_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="validator",
            name="数据验证AI",
            description="负责数据验证和格式检查",
            functions=["validate_data", "check_format", "sanitize_input"],
            responsibilities=["数据验证", "格式检查", "输入净化"],
            config={"validation_enabled": True, "strict_mode": False},
            collection_id=self.ensemble_id
        )
        self.sub_ais["validator"] = instance_id
        logger.info("数据验证AI实例化成功")
    
    def _init_log_analyzer_ai(self):
        """实例化日志分析AI"""
        instance_id = "log_analyzer_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="log_analyzer",
            name="日志分析AI",
            description="负责日志分析和异常检测",
            functions=["analyze_logs", "detect_anomalies", "generate_alerts"],
            responsibilities=["日志分析", "异常检测", "告警生成"],
            config={"analysis_enabled": True, "alert_threshold": 3},
            collection_id=self.ensemble_id
        )
        self.sub_ais["log_analyzer"] = instance_id
        logger.info("日志分析AI实例化成功")
    
    def _init_cleanup_ai(self):
        """实例化系统清理AI"""
        instance_id = "cleanup_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="cleanup",
            name="系统清理AI",
            description="负责系统资源清理和优化",
            functions=["cleanup_resources", "optimize_storage", "remove_temp_files"],
            responsibilities=["资源清理", "存储优化", "临时文件删除"],
            config={"cleanup_enabled": True, "cleanup_interval": 86400},
            collection_id=self.ensemble_id
        )
        self.sub_ais["cleanup"] = instance_id
        logger.info("系统清理AI实例化成功")
    
    def _init_theme_ai(self):
        """实例化主题配色AI"""
        instance_id = "theme_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="theme",
            name="主题配色AI",
            description="负责统一系统主题和配色方案",
            functions=["unify_theme", "optimize_ui", "adapt_styles"],
            responsibilities=["主题统一", "UI优化", "样式适配"],
            config={"theme_enabled": True, "supported_languages": ["japanese", "english"]},
            collection_id=self.ensemble_id
        )
        self.sub_ais["theme"] = instance_id
        logger.info("主题配色AI实例化成功")
    
    def _init_registration_ai(self):
        """实例化注册AI"""
        instance_id = "registration_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="registration",
            name="注册AI",
            description="负责处理用户注册流程，包括验证、处理和监控",
            functions=["register_user", "monitor_registration_process", "execute_registration_rules"],
            responsibilities=["用户注册", "注册监控", "规则执行"],
            config={"enabled": True, "require_email_verification": False},
            collection_id=self.ensemble_id
        )
        self.sub_ais["registration"] = instance_id
        logger.info("注册AI实例化成功")
    
    def _init_login_ai(self):
        """实例化登录AI"""
        instance_id = "login_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="login",
            name="登录AI",
            description="负责处理用户登录流程，包括验证、监控和统计",
            functions=["login_user", "get_login_stats", "get_user_login_history"],
            responsibilities=["用户登录", "登录监控", "登录统计"],
            config={"enabled": True, "max_login_attempts": 5},
            collection_id=self.ensemble_id
        )
        self.sub_ais["login"] = instance_id
        logger.info("登录AI实例化成功")
    
    def _init_question_bank_expander_ai(self):
        """实例化题库扩充AI"""
        instance_id = "question_bank_expander_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="question_bank_expander",
            name="题库扩充AI",
            description="负责自动从网络获取题目并扩充日语和英语题库",
            functions=["expand_question_bank", "auto_expand_all_categories", "get_expansion_stats"],
            responsibilities=["题库扩充", "自动更新", "统计分析"],
            config={"enabled": True, "auto_expand_interval": 3600, "language_support": ["japanese", "english"]},
            collection_id=self.ensemble_id
        )
        self.sub_ais["question_bank_expander"] = instance_id
        logger.info("题库扩充AI实例化成功")
    
    def _init_animation_fixer_ai(self):
        """实例化动画修复AI"""
        instance_id = "animation_fixer_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="animation_fixer",
            name="动画修复AI",
            description="专门用于修复过渡动画和极窄路动画的AI模块",
            functions=["analyze_and_fix_animations", "generate_animation_report"],
            responsibilities=["过渡动画修复", "极窄路动画修复", "动画分析报告生成"],
            config={"enabled": True, "auto_fix": True, "animation_types": ["transition", "narrow_road"]},
            collection_id=self.ensemble_id
        )
        self.sub_ais["animation_fixer"] = instance_id
        logger.info("动画修复AI实例化成功")
    
    def _init_version_manager_ai(self):
        """实例化版本管理AI"""
        instance_id = "version_manager_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="version_manager",
            name="版本管理AI",
            description="负责自动监控系统版本号、内部版本号和测试版本号",
            functions=["monitor_versions", "get_version_info", "update_version", "check_version_consistency"],
            responsibilities=["版本监控", "版本更新", "版本一致性检查", "版本历史管理"],
            config={"monitoring_enabled": True, "auto_update_enabled": False, "check_interval": 3600},
            collection_id=self.ensemble_id
        )
        self.sub_ais["version_manager"] = instance_id
        logger.info("版本管理AI实例化成功")
    
    def _init_backup_manager_ai(self):
        """实例化备份管理AI"""
        instance_id = "backup_manager_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="backup_manager",
            name="备份管理AI",
            description="负责系统备份和恢复功能",
            functions=["create_backup", "restore_backup", "get_backup_stats", "configure_auto_backup", "verify_backup"],
            responsibilities=["系统备份", "备份恢复", "备份统计", "自动备份配置", "备份验证"],
            config={"auto_backup_enabled": True, "backup_interval": 86400, "max_backup_count": 30},
            collection_id=self.ensemble_id
        )
        self.sub_ais["backup_manager"] = instance_id
        logger.info("备份管理AI实例化成功")

    def _init_rule_manager_ai(self):
        """实例化规则管理AI"""
        instance_id = "rule_manager_ai"
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="rule_manager",
            name="规则管理AI",
            description="负责管理和执行系统所有规则的AI模块",
            functions=["load_rules", "execute_rule", "execute_rules_by_type", "monitor_rules", "optimize_rules", "get_rule_stats"],
            responsibilities=["规则加载", "规则执行", "规则监控", "规则优化", "规则统计"],
            config={"monitoring_enabled": True, "auto_optimize_enabled": True},
            collection_id=self.ensemble_id
        )
        self.sub_ais["rule_manager"] = instance_id
        logger.info("规则管理AI实例化成功")

    def get_sub_ai(self, ai_type):
        """获取特定类型的子AI实例"""
        with self.lock:
            instance_id = self.sub_ais.get(ai_type)
            if instance_id:
                return ai_instance_manager.get_ai_instance(instance_id)
            logger.warning(f"未找到类型为 {ai_type} 的子AI")
            return None
    
    def get_all_sub_ais(self):
        """获取所有子AI实例"""
        with self.lock:
            return [ai_instance_manager.get_ai_instance(instance_id) for instance_id in self.sub_ais.values() if ai_instance_manager.get_ai_instance(instance_id)]
    
    def dispatch_task(self, task_type, task_data):
        """根据任务类型分配给合适的子AI，实现自我学习优化"""
        with self.lock:
            logger.info(f"AI集收到任务: {task_type}")
            
            # 根据任务类型选择合适的子AI
            ai_mapping = {
                "monitor": "monitoring",
                "learn": "learning",
                "optimize_route": "route_optimizer",
                "generate_question": "question_generator",
                "generate_test": "test_generator",
                "manage_sandbox": "sandbox_manager",
                "analyze_code": "code_analyzer",
                "supervise_test": "test_supervisor",
                "authenticate": "auth",
                "validate_data": "validator",
                "analyze_logs": "log_analyzer",
                "cleanup": "cleanup",
                "unify_theme": "theme",
                "register_user": "registration",
                "monitor_registration": "registration",
                "execute_registration_rules": "registration",
                "login_user": "login",
                "get_login_stats": "login",
                "get_user_login_history": "login",
                "expand_question_bank": "question_bank_expander",
                "auto_expand_all_categories": "question_bank_expander",
                "get_expansion_stats": "question_bank_expander",
                "fix_animations": "animation_fixer",
                "analyze_animations": "animation_fixer",
                "generate_animation_report": "animation_fixer",
                "monitor_versions": "version_manager",
                "get_version_info": "version_manager",
                "get_version_history": "version_manager",
                "update_version": "version_manager",
                "auto_update_versions": "version_manager",
                "check_version_consistency": "version_manager",
                "create_backup": "backup_manager",
                "restore_backup": "backup_manager",
                "get_backup_stats": "backup_manager",
                "configure_auto_backup": "backup_manager",
                "get_backup_history": "backup_manager",
                "delete_backup": "backup_manager",
                "verify_backup": "backup_manager",
                "create_auto_backup": "backup_manager",
                "cleanup_old_backups": "backup_manager",
                "load_rules": "rule_manager",
                "execute_rule": "rule_manager",
                "execute_rules_by_type": "rule_manager",
                "monitor_rules": "rule_manager",
                "optimize_rules": "rule_manager",
                "get_rule_stats": "rule_manager"
            }
            
            ai_type = ai_mapping.get(task_type)
            if ai_type:
                instance_id = self.sub_ais.get(ai_type)
                if instance_id:
                    logger.info(f"将任务 {task_type} 分配给 {ai_type} AI")
                    
                    # 记录任务分配历史，用于学习优化
                    task_record = {
                        "timestamp": time.time(),
                        "task_type": task_type,
                        "ai_type": ai_type,
                        "instance_id": instance_id,
                        "task_data": task_data,
                        "status": "assigned"
                    }
                    self.task_history.append(task_record)
                    
                    # 限制历史记录长度，避免内存占用过大
                    if len(self.task_history) > 1000:
                        self.task_history = self.task_history[-1000:]
                    
                    # 调用实际的AI功能
                    result = self._execute_ai_task(ai_type, task_type, task_data)
                    
                    # 更新任务状态
                    task_record["status"] = "completed"
                    task_record["result"] = result
                    
                    # 触发自我学习优化
                    self._trigger_self_learning()
                    
                    return result
                else:
                    logger.error(f"未找到类型为 {ai_type} 的子AI实例")
                    return {
                        "success": False,
                        "message": f"未找到类型为 {ai_type} 的子AI实例"
                    }
            else:
                logger.error(f"未找到适合任务类型 {task_type} 的子AI")
                return {
                    "success": False,
                    "message": f"未找到适合任务类型 {task_type} 的子AI"
                }
    
    def _execute_ai_task(self, ai_type, task_type, task_data):
        """执行实际的AI任务"""
        # 调用相应的AI实例执行任务
        if ai_type == "monitoring":
            return ai_monitor.monitor_system(task_data)
        elif ai_type == "learning":
            return ai_learning.self_learning(task_data)
        elif ai_type == "route_optimizer":
            return route_optimizer.optimize_routes(task_data)
        elif ai_type == "question_generator":
            return ai_question_generator.generate_questions_batch(**task_data)
        elif ai_type == "sandbox_manager":
            return sandbox_manager.create_sandbox(**task_data)
        elif ai_type == "code_analyzer":
            return ai_code_analyzer.analyze_code(task_data)
        elif ai_type == "auth":
            return auth_ai.authenticate_user(task_data)
        elif ai_type == "validator":
            return validator_ai.validate_data(task_data)
        elif ai_type == "log_analyzer":
            return log_analyzer_ai.analyze_logs(task_data)
        elif ai_type == "cleanup":
            return cleanup_ai.cleanup_resources(task_data)
        elif ai_type == "theme":
            return theme_ai.unify_theme(task_data)
        elif ai_type == "registration":
            return registration_ai.register_user(task_data)
        elif ai_type == "login":
            return login_ai.login_user(task_data)
        elif ai_type == "question_bank_expander":
            if task_type == "expand_question_bank":
                return ai_question_bank_expander.expand_question_bank(**task_data)
            elif task_type == "auto_expand_all_categories":
                return ai_question_bank_expander.auto_expand_all_categories()
            elif task_type == "get_expansion_stats":
                return ai_question_bank_expander.get_expansion_stats()
            else:
                return {
                    "success": False,
                    "message": f"未实现 {task_type} 任务的执行逻辑"
                }
        elif ai_type == "animation_fixer":
            if task_type == "fix_animations":
                return animation_fixer_ai.analyze_and_fix_animations(**task_data)
            elif task_type == "analyze_animations":
                return animation_fixer_ai.analyze_and_fix_animations(**task_data)
            elif task_type == "generate_animation_report":
                return animation_fixer_ai.generate_animation_report()
            else:
                return {
                    "success": False,
                    "message": f"未实现 {task_type} 任务的执行逻辑"
                }
        elif ai_type == "version_manager":
            if task_type == "monitor_versions":
                return version_manager_ai.monitor_versions()
            elif task_type == "get_version_info":
                return version_manager_ai.get_version_info()
            elif task_type == "get_version_history":
                limit = task_data.get('limit', 20)
                return version_manager_ai.get_version_history(limit)
            elif task_type == "update_version":
                version_type = task_data.get('version_type')
                new_version = task_data.get('new_version')
                return version_manager_ai.update_version(version_type, new_version)
            elif task_type == "auto_update_versions":
                return version_manager_ai.auto_update_versions()
            elif task_type == "check_version_consistency":
                return version_manager_ai.check_version_consistency()
            else:
                return {
                    "success": False,
                    "message": f"未实现 {task_type} 任务的执行逻辑"
                }
        elif ai_type == "backup_manager":
            if task_type == "create_backup":
                backup_name = task_data.get('name')
                backup_type = task_data.get('backup_type', 'full')
                description = task_data.get('description')
                created_by = task_data.get('created_by', 'system')
                return backup_manager_ai.create_backup(backup_name, backup_type, description, created_by)
            elif task_type == "restore_backup":
                backup_id = task_data.get('backup_id')
                return backup_manager_ai.restore_backup(backup_id)
            elif task_type == "get_backup_stats":
                return backup_manager_ai.get_backup_stats()
            elif task_type == "configure_auto_backup":
                enabled = task_data.get('enabled', True)
                interval_hours = task_data.get('interval_hours', 24)
                max_count = task_data.get('max_count', 30)
                return backup_manager_ai.configure_auto_backup(enabled, interval_hours, max_count)
            elif task_type == "get_backup_history":
                limit = task_data.get('limit', 50)
                offset = task_data.get('offset', 0)
                return backup_manager_ai.get_backup_history(limit, offset)
            elif task_type == "delete_backup":
                backup_id = task_data.get('backup_id')
                return backup_manager_ai.delete_backup(backup_id)
            elif task_type == "verify_backup":
                backup_id = task_data.get('backup_id')
                return backup_manager_ai.verify_backup(backup_id)
            elif task_type == "create_auto_backup":
                return backup_manager_ai.create_auto_backup()
            elif task_type == "cleanup_old_backups":
                return backup_manager_ai.cleanup_old_backups()
            else:
                return {
                    "success": False,
                    "message": f"未实现 {task_type} 任务的执行逻辑"
                }
        elif ai_type == "rule_manager":
            if task_type == "load_rules":
                return rule_manager_ai.load_rules()
            elif task_type == "execute_rule":
                rule_type = task_data.get('rule_type')
                rule_name = task_data.get('rule_name')
                kwargs = task_data.get('kwargs', {})
                return rule_manager_ai.execute_rule(rule_type, rule_name, **kwargs)
            elif task_type == "execute_rules_by_type":
                rule_type = task_data.get('rule_type')
                kwargs = task_data.get('kwargs', {})
                return rule_manager_ai.execute_rules_by_type(rule_type, **kwargs)
            elif task_type == "monitor_rules":
                return rule_manager_ai.monitor_rules()
            elif task_type == "optimize_rules":
                return rule_manager_ai.optimize_rules()
            elif task_type == "get_rule_stats":
                return rule_manager_ai.get_rule_stats()
            else:
                return {
                    "success": False,
                    "message": f"未实现 {task_type} 任务的执行逻辑"
                }
        else:
            return {
                "success": False,
                "message": f"未实现 {ai_type} AI的任务执行逻辑"
            }
    
    def _trigger_self_learning(self):
        """触发自我学习优化"""
        # 每10个任务触发一次自我学习
        if len(self.task_history) % 10 == 0:
            logger.info("触发AI集自我学习优化")
            self.optimize_ensemble()
            # 也可以触发学习AI进行更深入的学习
            if "learning" in self.sub_ais:
                ai_learning.self_learning({
                    "task_history": self.task_history[-50:],  # 最近50个任务
                    "ensemble_stats": self.get_ensemble_stats()
                })
    
    def update_sub_ai(self, ai_type, updates):
        """更新子AI配置"""
        with self.lock:
            instance_id = self.sub_ais.get(ai_type)
            if instance_id:
                return ai_instance_manager.update_ai_instance(instance_id, updates)
            logger.warning(f"未找到类型为 {ai_type} 的子AI")
            return False
    
    def refresh_ensemble(self):
        """刷新AI集状态"""
        with self.lock:
            # 从数据库刷新AI实例
            ai_instance_manager.refresh_from_db()
            
            # 更新AI集信息
            self.updated_at = time.time()
            logger.info("AI集已刷新")
            return True
    
    def get_ensemble_stats(self):
        """获取AI集统计信息"""
        with self.lock:
            sub_ais = self.get_all_sub_ais()
            active_ais = [ai for ai in sub_ais if ai and ai.get('status') == 'active']
            
            stats = {
                "ensemble_id": self.ensemble_id,
                "name": self.name,
                "total_sub_ais": len(sub_ais),
                "active_sub_ais": len(active_ais),
                "ai_types": list(self.sub_ais.keys()),
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "status": self.status
            }
            
            # 添加各类型AI的状态统计
            status_stats = {}
            for ai in sub_ais:
                if ai:
                    status = ai.get('status', 'unknown')
                    status_stats[status] = status_stats.get(status, 0) + 1
            stats["status_stats"] = status_stats
            
            return stats
    
    def optimize_ensemble(self):
        """优化AI集配置，确保各子AI深度匹配系统需求和项目功能"""
        with self.lock:
            logger.info("开始优化AI集配置")
            
            # 1. 重新检测项目功能，确保AI集与项目保持同步
            new_features = self._detect_project_features()
            if set(new_features) != set(self.project_features):
                logger.info(f"项目功能发生变化: 旧功能={self.project_features}, 新功能={new_features}")
                self.project_features = new_features
                self.required_ai_types = self._determine_required_ai_types()
                
                # 根据新的项目功能调整AI实例
                self._adapt_to_project_changes()
            
            # 2. 基于任务历史和AI使用情况优化配置
            usage_stats = self._analyze_ai_usage()
            
            # 3. 生成AI间协调配置，增强AI间的通信和协作
            coordination_config = self._generate_coordination_config()
            
            # 4. 更新每个子AI的配置，使其更好地匹配系统需求
            for ai_type, instance_id in self.sub_ais.items():
                instance = ai_instance_manager.get_ai_instance(instance_id)
                if instance:
                    # 根据系统需求、项目功能和使用情况优化子AI配置
                    optimized_config = self._optimize_ai_config(ai_type, instance['config'], usage_stats)
                    
                    # 添加AI间协调配置
                    optimized_config['coordination'] = coordination_config.get(ai_type, {})
                    
                    if optimized_config:
                        ai_instance_manager.update_ai_instance(instance_id, {"config": optimized_config})
                        logger.info(f"已优化 {ai_type} AI的配置")
            
            # 5. 优化AI集的资源分配
            self._optimize_resource_allocation()
            
            # 6. 更新AI集的协调机制
            self._update_coordination_mechanism()
            
            self.updated_at = time.time()
            logger.info("AI集配置优化完成")
            return True
    
    def _adapt_to_project_changes(self):
        """动态适应项目功能变化"""
        logger.info("开始动态适应项目功能变化")
        
        # 检查当前实例化的AI类型
        current_ai_types = set(self.sub_ais.keys())
        required_ai_types = set(self.required_ai_types)
        
        # 识别需要新增的AI类型
        ai_types_to_add = required_ai_types - current_ai_types
        # 识别需要移除的AI类型
        ai_types_to_remove = current_ai_types - required_ai_types
        
        # 添加新的AI类型
        if ai_types_to_add:
            logger.info(f"需要新增AI类型: {ai_types_to_add}")
            init_methods = {
                'monitoring': self._init_monitoring_ai,
                'learning': self._init_learning_ai,
                'route_optimizer': self._init_route_optimizer_ai,
                'question_generator': self._init_question_generator_ai,
                'test_generator': self._init_test_generator_ai,
                'sandbox_manager': self._init_sandbox_manager_ai,
                'code_analyzer': self._init_code_analyzer_ai,
                'test_supervisor': self._init_test_supervisor_ai,
                'auth': self._init_auth_ai,
                'validator': self._init_validator_ai,
                'log_analyzer': self._init_log_analyzer_ai,
                'cleanup': self._init_cleanup_ai,
                'theme': self._init_theme_ai,
                'registration': self._init_registration_ai,
                'login': self._init_login_ai,
                'question_bank_expander': self._init_question_bank_expander_ai,
                'animation_fixer': self._init_animation_fixer_ai,
                'version_manager': self._init_version_manager_ai,
                'backup_manager': self._init_backup_manager_ai,
                'rule_manager': self._init_rule_manager_ai
            }
            
            for ai_type in ai_types_to_add:
                if ai_type in init_methods:
                    try:
                        init_methods[ai_type]()
                    except Exception as e:
                        logger.error(f"实例化 {ai_type} AI失败: {str(e)}")
        
        # 移除不再需要的AI类型
        if ai_types_to_remove:
            logger.info(f"需要移除AI类型: {ai_types_to_remove}")
            for ai_type in ai_types_to_remove:
                instance_id = self.sub_ais.pop(ai_type, None)
                if instance_id:
                    # 这里可以添加AI实例清理逻辑
                    logger.info(f"已移除 {ai_type} AI实例")
        
        logger.info("动态适应项目功能变化完成")
    
    def _analyze_ai_usage(self):
        """分析AI使用情况"""
        usage_stats = {}
        
        # 统计各AI类型的使用次数
        for ai_type in self.sub_ais.keys():
            usage_stats[ai_type] = {
                "task_count": 0,
                "success_count": 0,
                "average_response_time": 0.0
            }
        
        # 分析任务历史
        if self.task_history:
            for task in self.task_history:
                ai_type = task.get("ai_type")
                if ai_type in usage_stats:
                    usage_stats[ai_type]["task_count"] += 1
                    if task.get("result", {}).get("success", False):
                        usage_stats[ai_type]["success_count"] += 1
        
        return usage_stats
    
    def _generate_coordination_config(self):
        """生成AI间协调配置，增强AI间的通信和协作"""
        coordination_config = {}
        
        # 为每个AI类型配置协调参数
        for ai_type in self.sub_ais.keys():
            coordination_config[ai_type] = {
                "communication_enabled": True,
                "collaboration_partners": self._get_collaboration_partners(ai_type),
                "message_queue_enabled": True,
                "shared_memory_enabled": True,
                "event_bus_enabled": True,
                "priority": 50  # 默认优先级
            }
        
        return coordination_config
    
    def _get_collaboration_partners(self, ai_type):
        """获取AI类型的协作伙伴"""
        collaboration_map = {
            "monitoring": ["log_analyzer", "cleanup", "version_manager"],
            "log_analyzer": ["monitoring", "auth"],
            "auth": ["monitoring", "registration", "login"],
            "registration": ["auth", "monitoring"],
            "login": ["auth", "monitoring"],
            "learning": ["question_generator", "test_generator"],
            "question_generator": ["learning", "test_generator", "question_bank_expander"],
            "test_generator": ["learning", "question_generator"],
            "question_bank_expander": ["question_generator"],
            "code_analyzer": ["monitoring"],
            "theme": ["monitoring"],
            "animation_fixer": ["monitoring"],
            "sandbox_manager": ["monitoring", "cleanup"],
            "cleanup": ["monitoring", "sandbox_manager"],
            "route_optimizer": ["monitoring"],
            "version_manager": ["monitoring"],
            "rule_manager": ["monitoring", "log_analyzer", "cleanup"]
        }
        return collaboration_map.get(ai_type, [])
    
    def _optimize_resource_allocation(self):
        """优化AI集的资源分配"""
        logger.info("开始优化AI集资源分配")
        
        # 基于AI使用情况调整资源分配
        usage_stats = self._analyze_ai_usage()
        
        for ai_type, stats in usage_stats.items():
            # 根据使用情况调整AI资源优先级
            if stats["task_count"] > 50:
                # 高使用率AI，提高资源优先级
                self.update_sub_ai(ai_type, {"priority": 20})
            elif stats["task_count"] < 10:
                # 低使用率AI，降低资源优先级
                self.update_sub_ai(ai_type, {"priority": 80})
            
        logger.info("AI集资源分配优化完成")
    
    def _update_coordination_mechanism(self):
        """更新AI集的协调机制"""
        logger.info("开始更新AI集协调机制")
        
        # 这里可以添加AI间协调机制的更新逻辑
        # 例如：更新消息队列配置、事件总线配置等
        
        # 检查AI间通信通道状态
        for ai_type in self.sub_ais.keys():
            # 模拟检查AI通信通道
            logger.info(f"检查 {ai_type} AI的通信通道状态")
        
        logger.info("AI集协调机制更新完成")
    
    def call_external_ai_engine(self, engine_type, prompt, **kwargs):
        """调用外部AI引擎生成回复
        
        Args:
            engine_type: AI引擎类型，支持：volcengine(抖音火山引擎), doubao(豆包), tencent(腾讯云), aliyun(阿里云), afu(阿福), qianwen(千问)
            prompt: 提示词
            **kwargs: 其他参数，如temperature, max_tokens等
            
        Returns:
            dict: AI引擎回复结果
        """
        logger.info(f"调用外部AI引擎: {engine_type}")
        
        try:
            result = ai_engine_integrator.call_engine(engine_type, prompt, **kwargs)
            if result:
                logger.info(f"外部AI引擎 {engine_type} 调用成功")
            else:
                logger.error(f"外部AI引擎 {engine_type} 调用失败")
            return result
        except Exception as e:
            logger.error(f"调用外部AI引擎 {engine_type} 异常: {str(e)}")
            return None
    
    def get_supported_ai_engines(self):
        """获取支持的外部AI引擎列表"""
        return ai_engine_integrator.get_supported_engines()
    
    def configure_ai_engine(self, engine_type, config):
        """配置外部AI引擎"""
        return ai_engine_integrator.configure_engine(engine_type, config)
    
    def get_ai_engine_config(self, engine_type):
        """获取外部AI引擎配置"""
        return ai_engine_integrator.get_engine_config(engine_type)
    
    def _optimize_ai_config(self, ai_type, current_config, usage_stats):
        """根据AI类型、使用情况和项目功能优化配置"""
        optimized_config = current_config.copy()
        
        # 获取AI使用统计
        ai_usage = usage_stats.get(ai_type, {})
        task_count = ai_usage.get("task_count", 0)
        success_rate = ai_usage.get("success_count", 0) / max(1, task_count)
        
        # 基础优化配置，适用于所有AI类型
        base_optimizations = {
            "active": True,
            "auto_optimize": True,
            "monitoring_enabled": "monitoring" in self.required_ai_types,
            "error_reporting_enabled": True,
            "log_level": "INFO" if "debug" in self.project_features else "WARN"
        }
        optimized_config.update(base_optimizations)
        
        # 针对不同类型的AI进行特定优化
        if ai_type == "monitoring":
            # 根据项目功能和使用情况优化监控AI配置
            optimized_config.update({
                "monitoring_frequency": 60 if "monitoring" in self.required_ai_types else 300,  # 根据是否需要监控功能调整频率
                "error_threshold": 3,
                "alert_enabled": True,
                "monitored_features": self.project_features,  # 监控与项目功能相关的内容
                "alert_channels": ["log", "email"],
                "alert_recipients": ["admin@example.com"],
                "performance_monitoring_enabled": True,
                "resource_monitoring_enabled": True
            })
        elif ai_type == "learning":
            # 根据使用情况优化学习AI配置
            learning_rate = 0.01
            batch_size = 32
            
            # 如果成功率低，调整学习参数
            if success_rate < 0.7:
                learning_rate = 0.005
                batch_size = 16
            elif task_count > 100:
                # 任务量大时，调整学习参数以提高效率
                learning_rate = 0.02
                batch_size = 64
            
            optimized_config.update({
                "learning_rate": learning_rate,
                "batch_size": batch_size,
                "optimization_interval": 3600,
                "learning_enabled": True,
                "knowledge_retention_enabled": True,
                "transfer_learning_enabled": "testing" in self.required_ai_types,
                "model_checkpoint_enabled": True
            })
        elif ai_type == "test_generator":
            # 根据项目功能优化测试生成AI配置
            optimized_config.update({
                "question_count": 20,
                "difficulty_levels": [1, 2, 3, 4, 5],
                "supported_languages": ["japanese", "english"],
                "auto_adjust_difficulty": True,
                "user_analysis_enabled": "learning" in self.required_ai_types,  # 如果有学习功能，启用用户分析
                "variety_optimization_enabled": True,
                "topic_diversity_enabled": True,
                "difficulty_balance_enabled": True
            })
        elif ai_type == "theme":
            # 根据项目功能优化主题AI配置
            optimized_config.update({
                "unified_theme": True,
                "color_scheme": "modern",
                "responsive_design": True,
                "supported_languages": ["japanese", "english"],
                "theme_enabled": "theme_management" in self.required_ai_types,
                "dark_mode_support": True,
                "contrast_optimization": True,
                "accessibility_enabled": True
            })
        elif ai_type == "registration":
            # 根据使用情况优化注册AI配置
            optimized_config.update({
                "enabled": "user_management" in self.required_ai_types,
                "require_email_verification": False,
                "max_attempts_per_ip": 10,
                "cooldown_period": 3600,
                "block_suspicious_ips": True,
                "auto_optimize_rules": True,
                "registration_monitoring_enabled": True,
                "fraud_detection_enabled": True,
                "ai_notification_enabled": True
            })
        elif ai_type == "login":
            # 根据使用情况优化登录AI配置
            optimized_config.update({
                "enabled": "user_management" in self.required_ai_types,
                "max_login_attempts": 5,
                "lockout_duration": 1800,
                "allow_guest_login": True,
                "two_factor_enabled": False,
                "login_monitoring_enabled": "monitoring" in self.required_ai_types,
                "brute_force_protection_enabled": True,
                "login_history_enabled": True
            })
        elif ai_type == "rule_manager":
            # 根据使用情况优化规则管理AI配置
            optimized_config.update({
                "enabled": "rule_management" in self.required_ai_types,
                "monitoring_enabled": "monitoring" in self.required_ai_types,
                "auto_optimize_enabled": success_rate > 0.8,
                "monitoring_interval": 300,  # 5分钟
                "auto_optimize_interval": 3600,  # 1小时
                "rule_execution_history_limit": 1000,
                "error_threshold": 3,
                "alert_enabled": True
            })
        elif ai_type == "question_generator":
            # 根据项目功能和使用情况优化问题生成AI配置
            optimized_config.update({
                "auto_generate": True,
                "language_support": ["japanese", "english"],
                "quality_optimization_enabled": True,
                "difficulty_adjustment_enabled": "learning" in self.required_ai_types,
                "duplicate_detection_enabled": True,
                "similarity_threshold": 0.5,  # 使用优化后的相似度阈值
                "max_generation_attempts": 10,  # 增加最大尝试次数
                "variant_generation_enabled": True,  # 启用变体生成，增加题目多样性
                "question_diversity_enabled": True,
                "difficulty_range": [1, 5],
                "topic_coverage_enabled": True
            })
        elif ai_type == "cleanup":
            # 根据系统资源使用情况优化清理AI配置
            optimized_config.update({
                "cleanup_enabled": True,
                "cleanup_interval": 86400,
                "optimize_storage": True,
                "remove_temp_files": True,
                "database_cleanup_enabled": True,
                "log_cleanup_enabled": True,
                "cache_cleanup_enabled": True,
                "backup_before_cleanup": True
            })
        elif ai_type == "sandbox_manager":
            # 根据使用情况优化沙盒管理AI配置
            optimized_config.update({
                "sandbox_enabled": True,
                "dynamic_sandbox": {
                    "enabled": True,
                    "min_sandboxes": 5,
                    "max_sandboxes": 50,
                    "adjustment_step": 5
                },
                "auto_cleanup_sandboxes": True,
                "sandbox_isolation_level": "high",
                "sandbox_resource_limits": {
                    "cpu": "1000m",
                    "memory": "512Mi",
                    "disk": "1Gi"
                },
                "sandbox_timeout": 3600,
                "sandbox_monitoring_enabled": True
            })
        elif ai_type == "question_bank_expander":
            # 根据使用情况优化题库扩充AI配置
            optimized_config.update({
                "expansion_enabled": True,
                "min_questions_per_category": 20,
                "min_vocab_questions": 40,
                "request_rate": 1,
                "max_attempts": 5,
                "language_support": ["japanese", "english"],
                "auto_expand_interval": 3600,  # 每小时自动扩充一次题库
                "quality_filtering_enabled": True,
                "duplicate_checking_enabled": True,
                "category_balance_enabled": True
            })
        elif ai_type == "animation_fixer":
            # 根据使用情况优化动画修复AI配置
            optimized_config.update({
                "animation_enabled": True,
                "auto_fix": True,
                "animation_types": ["transition", "narrow_road", "loading", "hover"],
                "scan_interval": 3600,  # 每小时扫描一次动画问题
                "performance_optimization_enabled": True,
                "accessibility_fixes_enabled": True,
                "cross_browser_compatibility_enabled": True
            })
        elif ai_type == "code_analyzer":
            # 根据使用情况优化代码分析AI配置
            optimized_config.update({
                "analysis_enabled": True,
                "auto_fix": False,
                "code_quality_checks": ["style", "security", "performance"],
                "language_support": ["python", "javascript", "html", "css"],
                "report_format": "json",
                "report_generation_enabled": True
            })
        elif ai_type == "route_optimizer":
            # 根据使用情况优化路由优化AI配置
            optimized_config.update({
                "optimization_enabled": True,
                "check_interval": 600,
                "load_balancing_enabled": True,
                "performance_monitoring_enabled": True,
                "auto_adjust_routes": True
            })
        elif ai_type == "version_manager":
            # 根据使用情况优化版本管理AI配置
            optimized_config.update({
                "monitoring_enabled": True,
                "auto_update_enabled": False,
                "check_interval": 3600,
                "version_file_enabled": True,
                "history_enabled": True,
                "consistency_check_enabled": True,
                "log_level": "INFO"
            })
        elif ai_type == "backup_manager":
            # 根据使用情况优化备份管理AI配置
            optimized_config.update({
                "auto_backup_enabled": True,
                "backup_interval": 86400,
                "max_backup_count": 30,
                "backup_types": ["full", "incremental"],
                "auto_cleanup_enabled": True,
                "backup_verification_enabled": True,
                "log_level": "INFO"
            })
        
        return optimized_config

# 初始化主AI集
ai_ensemble = AIEnsemble()
