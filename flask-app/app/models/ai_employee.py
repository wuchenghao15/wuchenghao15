# -*- coding: utf-8 -*-
"""
AI员工模型
用于自动修复代码错误、异常和逻辑漏洞的AI员工系统
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, Enum, JSON
from app.models.base_model import BaseModel
import enum

class AIEmployeeStatus(enum.Enum):
    """AI员工状态"""
    ACTIVE = "active"              # 运行中
    INACTIVE = "inactive"          # 未激活
    TRAINING = "training"          # 训练中
    ERROR = "error"                # 错误状态
    MAINTENANCE = "maintenance"     # 维护中

class ErrorSeverity(enum.Enum):
    """错误严重程度"""
    CRITICAL = "critical"           # 严重
    HIGH = "high"                  # 高
    MEDIUM = "medium"              # 中
    LOW = "low"                   # 低
    INFO = "info"                  # 信息

class ErrorCategory(enum.Enum):
    """错误类别"""
    SYNTAX = "syntax"                      # 语法错误
    RUNTIME = "runtime"                    # 运行时错误
    LOGIC = "logic"                        # 逻辑错误
    MATHEMATICAL = "mathematical"          # 数学错误
    DIVISION_BY_ZERO = "division_by_zero"  # 除零错误
    NEGATIVE_SQUARE_ROOT = "negative_square_root"  # 负数平方根
    QUADRATIC_NEGATIVE_DISCRIMINANT = "quadratic_negative_discriminant"  # 求根公式负判别式
    NULL_POINTER = "null_pointer"          # 空指针
    TYPE_MISMATCH = "type_mismatch"         # 类型不匹配
    INDEX_OUT_OF_BOUNDS = "index_out_of_bounds"  # 索引越界
    FILE_NOT_FOUND = "file_not_found"       # 文件未找到
    PERMISSION_DENIED = "permission_denied" # 权限拒绝
    NETWORK_ERROR = "network_error"         # 网络错误
    DATABASE_ERROR = "database_error"       # 数据库错误
    UNHANDLED_EXCEPTION = "unhandled_exception"  # 未处理异常
    CUSTOM = "custom"                       # 自定义错误

class SolutionStatus(enum.Enum):
    """解决方案状态"""
    PENDING = "pending"              # 待处理
    APPROVED = "approved"           # 已批准
    REJECTED = "rejected"          # 已拒绝
    IMPROVED = "improved"           # 已改进
    DEPLOYED = "deployed"           # 已部署

class AIEmployee(BaseModel):
    """AI员工模型"""
    __tablename__ = 'ai_employees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='AI员工名称')
    employee_code = Column(String(50), unique=True, nullable=False, comment='员工编号')
    description = Column(Text, comment='AI员工描述')
    capabilities = Column(JSON, comment='AI能力列表')
    specialties = Column(JSON, comment='专业领域')
    
    # 状态和性能
    status = Column(Enum(AIEmployeeStatus), default=AIEmployeeStatus.ACTIVE, comment='状态')
    accuracy = Column(Float, default=0.0, comment='准确率')
    total_tasks = Column(Integer, default=0, comment='总任务数')
    successful_fixes = Column(Integer, default=0, comment='成功修复数')
    failed_fixes = Column(Integer, default=0, comment='失败修复数')
    
    # 学习相关
    learning_rate = Column(Float, default=0.001, comment='学习率')
    knowledge_base_size = Column(Integer, default=0, comment='知识库大小')
    last_training = Column(DateTime, comment='最后训练时间')
    model_version = Column(String(50), comment='模型版本')
    
    # 配置
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    priority = Column(Integer, default=0, comment='优先级')
    max_concurrent_tasks = Column(Integer, default=5, comment='最大并发任务数')
    
    # 元数据
    created_by = Column(Integer, comment='创建者ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<AIEmployee {self.name} ({self.employee_code})>'
    
    @property
    def success_rate(self):
        """计算成功率"""
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_fixes / self.total_tasks) * 100
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'employee_code': self.employee_code,
            'description': self.description,
            'capabilities': self.capabilities or [],
            'specialties': self.specialties or [],
            'status': self.status.value if self.status else None,
            'accuracy': self.accuracy,
            'total_tasks': self.total_tasks,
            'successful_fixes': self.successful_fixes,
            'failed_fixes': self.failed_fixes,
            'success_rate': self.success_rate,
            'learning_rate': self.learning_rate,
            'knowledge_base_size': self.knowledge_base_size,
            'last_training': self.last_training.isoformat() if self.last_training else None,
            'model_version': self.model_version,
            'is_enabled': self.is_enabled,
            'priority': self.priority,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ErrorType(BaseModel):
    """错误类型模型"""
    __tablename__ = 'error_types'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='错误类型名称')
    code = Column(String(50), unique=True, nullable=False, comment='错误代码')
    category = Column(Enum(ErrorCategory), nullable=False, comment='错误类别')
    severity = Column(Enum(ErrorSeverity), default=ErrorSeverity.MEDIUM, comment='严重程度')
    description = Column(Text, comment='错误描述')
    patterns = Column(JSON, comment='匹配模式')
    keywords = Column(JSON, comment='关键词')
    
    # 检测和修复配置
    auto_detect = Column(Boolean, default=True, comment='是否自动检测')
    auto_fix = Column(Boolean, default=False, comment='是否自动修复')
    requires_approval = Column(Boolean, default=True, comment='是否需要审批')
    
    # 示例
    example_code = Column(Text, comment='错误代码示例')
    correct_code = Column(Text, comment='正确代码示例')
    
    # 统计
    occurrence_count = Column(Integer, default=0, comment='出现次数')
    fix_success_rate = Column(Float, default=0.0, comment='修复成功率')
    
    # 元数据
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<ErrorType {self.name} ({self.code})>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category': self.category.value if self.category else None,
            'severity': self.severity.value if self.severity else None,
            'description': self.description,
            'patterns': self.patterns or [],
            'keywords': self.keywords or [],
            'auto_detect': self.auto_detect,
            'auto_fix': self.auto_fix,
            'requires_approval': self.requires_approval,
            'example_code': self.example_code,
            'correct_code': self.correct_code,
            'occurrence_count': self.occurrence_count,
            'fix_success_rate': self.fix_success_rate,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Solution(BaseModel):
    """解决方案模型"""
    __tablename__ = 'solutions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment='解决方案标题')
    error_type_id = Column(Integer, comment='错误类型ID')
    ai_employee_id = Column(Integer, comment='AI员工ID')
    
    # 问题描述
    problem_description = Column(Text, nullable=False, comment='问题描述')
    problem_code = Column(Text, comment='问题代码')
    error_message = Column(Text, comment='错误信息')
    
    # 解决方案
    solution_code = Column(Text, nullable=False, comment='解决方案代码')
    explanation = Column(Text, comment='解决方案说明')
    steps = Column(JSON, comment='解决步骤')
    
    # 状态和验证
    status = Column(Enum(SolutionStatus), default=SolutionStatus.PENDING, comment='状态')
    is_verified = Column(Boolean, default=False, comment='是否已验证')
    is_tested = Column(Boolean, default=False, comment='是否已测试')
    test_results = Column(JSON, comment='测试结果')
    
    # 效果评估
    fix_success = Column(Boolean, default=False, comment='修复是否成功')
    performance_impact = Column(String(50), comment='性能影响')
    side_effects = Column(JSON, comment='副作用')
    
    # 学习相关
    confidence_score = Column(Float, default=0.0, comment='置信度分数')
    similar_cases_count = Column(Integer, default=0, comment='相似案例数')
    success_count = Column(Integer, default=0, comment='成功次数')
    failure_count = Column(Integer, default=0, comment='失败次数')
    
    # 元数据
    created_by = Column(Integer, comment='创建者ID')
    approved_by = Column(Integer, comment='审批者ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    deployed_at = Column(DateTime, comment='部署时间')
    
    def __repr__(self):
        return f'<Solution {self.title} ({self.id})>'
    
    @property
    def success_rate(self):
        """计算成功率"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'error_type_id': self.error_type_id,
            'ai_employee_id': self.ai_employee_id,
            'problem_description': self.problem_description,
            'problem_code': self.problem_code,
            'error_message': self.error_message,
            'solution_code': self.solution_code,
            'explanation': self.explanation,
            'steps': self.steps or [],
            'status': self.status.value if self.status else None,
            'is_verified': self.is_verified,
            'is_tested': self.is_tested,
            'test_results': self.test_results,
            'fix_success': self.fix_success,
            'performance_impact': self.performance_impact,
            'side_effects': self.side_effects or [],
            'confidence_score': self.confidence_score,
            'similar_cases_count': self.similar_cases_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_rate,
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None
        }


class FixTask(BaseModel):
    """修复任务模型"""
    __tablename__ = 'fix_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_code = Column(String(50), unique=True, nullable=False, comment='任务编号')
    error_type_id = Column(Integer, comment='错误类型ID')
    ai_employee_id = Column(Integer, nullable=False, comment='AI员工ID')
    
    # 问题描述
    source_file = Column(String(500), comment='源文件路径')
    source_code = Column(Text, nullable=False, comment='源代码')
    error_line = Column(Integer, comment='错误行号')
    error_message = Column(Text, comment='错误信息')
    
    # 修复结果
    fixed_code = Column(Text, comment='修复后代码')
    solution_id = Column(Integer, comment='解决方案ID')
    
    # 状态
    status = Column(String(50), default='pending', comment='任务状态')
    priority = Column(Integer, default=0, comment='优先级')
    
    # 执行信息
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    execution_time = Column(Float, comment='执行时间（秒）')
    
    # 结果
    is_successful = Column(Boolean, default=False, comment='是否成功')
    error_details = Column(Text, comment='错误详情')
    warnings = Column(JSON, comment='警告信息')
    
    # 反馈
    user_feedback = Column(Text, comment='用户反馈')
    rating = Column(Integer, comment='评分（1-5）')
    
    # 元数据
    created_by = Column(Integer, comment='创建者ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<FixTask {self.task_code}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_code': self.task_code,
            'error_type_id': self.error_type_id,
            'ai_employee_id': self.ai_employee_id,
            'source_file': self.source_file,
            'source_code': self.source_code,
            'error_line': self.error_line,
            'error_message': self.error_message,
            'fixed_code': self.fixed_code,
            'solution_id': self.solution_id,
            'status': self.status,
            'priority': self.priority,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time': self.execution_time,
            'is_successful': self.is_successful,
            'error_details': self.error_details,
            'warnings': self.warnings or [],
            'user_feedback': self.user_feedback,
            'rating': self.rating,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class LearningRecord(BaseModel):
    """学习记录模型"""
    __tablename__ = 'learning_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_employee_id = Column(Integer, nullable=False, comment='AI员工ID')
    solution_id = Column(Integer, comment='解决方案ID')
    fix_task_id = Column(Integer, comment='修复任务ID')
    
    # 学习内容
    input_data = Column(Text, comment='输入数据')
    output_data = Column(Text, comment='输出数据')
    expected_output = Column(Text, comment='期望输出')
    
    # 学习结果
    is_correct = Column(Boolean, default=False, comment='是否正确')
    error_type = Column(String(100), comment='错误类型')
    error_details = Column(Text, comment='错误详情')
    
    # 学习指标
    loss_value = Column(Float, comment='损失值')
    accuracy = Column(Float, comment='准确率')
    learning_time = Column(Float, comment='学习时间（秒）')
    
    # 模型更新
    model_version_before = Column(String(50), comment='更新前模型版本')
    model_version_after = Column(String(50), comment='更新后模型版本')
    
    # 元数据
    learning_type = Column(String(50), comment='学习类型')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<LearningRecord {self.id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'ai_employee_id': self.ai_employee_id,
            'solution_id': self.solution_id,
            'fix_task_id': self.fix_task_id,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'expected_output': self.expected_output,
            'is_correct': self.is_correct,
            'error_type': self.error_type,
            'error_details': self.error_details,
            'loss_value': self.loss_value,
            'accuracy': self.accuracy,
            'learning_time': self.learning_time,
            'model_version_before': self.model_version_before,
            'model_version_after': self.model_version_after,
            'learning_type': self.learning_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 创建数据库表
def init_ai_employee_tables(db):
    """初始化AI员工相关的数据库表"""
    # 创建表
    db.create_all()
    
    # 初始化默认的错误类型
    init_default_error_types(db)
    
    # 初始化默认的AI员工
    init_default_ai_employees(db)


def init_default_error_types(db):
    """初始化默认的错误类型"""
    default_errors = [
        {
            'name': '除零错误',
            'code': 'DIV_ZERO',
            'category': ErrorCategory.DIVISION_BY_ZERO,
            'severity': ErrorSeverity.HIGH,
            'description': '检测到除数为零的错误',
            'keywords': ['division by zero', '/0', 'mod by zero', '除以零', '除数为零'],
            'patterns': [
                r'/\s*0',
                r'div\s+0',
                r'mod\s+0',
                r'%\s*0'
            ],
            'auto_detect': True,
            'auto_fix': True,
            'requires_approval': True
        },
        {
            'name': '负数平方根',
            'code': 'NEG_SQRT',
            'category': ErrorCategory.NEGATIVE_SQUARE_ROOT,
            'severity': ErrorSeverity.HIGH,
            'description': '尝试对负数求平方根（复数i除外）',
            'keywords': ['square root of negative', 'sqrt(-', 'math domain error', '负数平方根'],
            'patterns': [
                r'sqrt\s*\(\s*-',
                r'Math\.sqrt\s*\(\s*-',
                r'np\.sqrt\s*\(\s*-',
                r'math\.sqrt\s*\(\s*-'
            ],
            'auto_detect': True,
            'auto_fix': True,
            'requires_approval': True
        },
        {
            'name': '求根公式负判别式',
            'code': 'QUAD_NEG_DISC',
            'category': ErrorCategory.QUADRATIC_NEGATIVE_DISCRIMINANT,
            'severity': ErrorSeverity.MEDIUM,
            'description': '二次方程求根公式中判别式小于零',
            'keywords': ['quadratic discriminant', 'b²-4ac', 'delta negative', '求根公式'],
            'patterns': [
                r'b\s*\*\s*b\s*-\s*4\s*\*\s*a\s*\*\s*c',
                r'delta\s*<\s*0',
                r'D\s*<\s*0',
                r' discriminant .* < 0'
            ],
            'auto_detect': True,
            'auto_fix': True,
            'requires_approval': False
        },
        {
            'name': '空指针引用',
            'code': 'NULL_PTR',
            'category': ErrorCategory.NULL_POINTER,
            'severity': ErrorSeverity.CRITICAL,
            'description': '尝试访问空对象或未初始化的变量',
            'keywords': ['null pointer', 'NoneType', 'undefined', 'is None', '空指针'],
            'patterns': [
                r'NoneType',
                r'null reference',
                r'cannot read property',
                r'\.is None',
                r'is None'
            ],
            'auto_detect': True,
            'auto_fix': False,
            'requires_approval': True
        },
        {
            'name': '类型不匹配',
            'code': 'TYPE_ERR',
            'category': ErrorCategory.TYPE_MISMATCH,
            'severity': ErrorSeverity.MEDIUM,
            'description': '数据类型不兼容或类型转换错误',
            'keywords': ['TypeError', 'type mismatch', 'cannot convert', '类型错误'],
            'patterns': [
                r'TypeError',
                r'type mismatch',
                r'cannot convert',
                r'invalid type'
            ],
            'auto_detect': True,
            'auto_fix': False,
            'requires_approval': True
        },
        {
            'name': '索引越界',
            'code': 'INDEX_ERR',
            'category': ErrorCategory.INDEX_OUT_OF_BOUNDS,
            'severity': ErrorSeverity.HIGH,
            'description': '数组或列表索引超出范围',
            'keywords': ['index error', 'IndexError', 'out of bounds', '越界'],
            'patterns': [
                r'IndexError',
                r'index out of range',
                r'list index out of range',
                r'array index out of bounds'
            ],
            'auto_detect': True,
            'auto_fix': False,
            'requires_approval': True
        },
        {
            'name': '未处理异常',
            'code': 'UNHANDLED_EXC',
            'category': ErrorCategory.UNHANDLED_EXCEPTION,
            'severity': ErrorSeverity.HIGH,
            'description': '代码抛出但未捕获的异常',
            'keywords': ['unhandled exception', 'raise', 'RuntimeError', 'Exception', '未处理异常'],
            'patterns': [
                r'raise\s+\w+Error',
                r'RuntimeError',
                r'Exception',
                r'unhandled exception'
            ],
            'auto_detect': True,
            'auto_fix': False,
            'requires_approval': True
        },
        {
            'name': '逻辑错误',
            'code': 'LOGIC_ERR',
            'category': ErrorCategory.LOGIC,
            'severity': ErrorSeverity.MEDIUM,
            'description': '代码逻辑错误，可能导致意外行为',
            'keywords': ['logic error', 'off-by-one', 'infinite loop', '逻辑错误'],
            'patterns': [
                r'infinite loop',
                r'off.by.one',
                r'logic error',
                r'incorrect logic'
            ],
            'auto_detect': False,
            'auto_fix': False,
            'requires_approval': True
        },
        {
            'name': 'CDN加载失败',
            'code': 'CDN_LOAD_FAIL',
            'category': ErrorCategory.NETWORK_ERROR,
            'severity': ErrorSeverity.HIGH,
            'description': '外部CDN资源加载失败，如Font Awesome等',
            'keywords': ['CDN', 'fontawesome', 'font-awesome', 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com', '资源加载', '图标显示'],
            'patterns': [
                r'font.*\.css',
                r'font.*\.js',
                r'cdn\.',
                r'ERR_ABORTED',
                r'net::ERR'
            ],
            'auto_detect': True,
            'auto_fix': True,
            'requires_approval': False
        },
        {
            'name': '图标显示失败',
            'code': 'ICON_SHOW_FAIL',
            'category': ErrorCategory.CUSTOM,
            'severity': ErrorSeverity.MEDIUM,
            'description': '网页图标无法显示失败',
            'keywords': ['图标', 'icon', 'missing icon', 'no icon', '显示失败'],
            'patterns': [
                r'<i.*class.*fa-',
                r'fa-icon',
                r'mdi-'
            ],
            'auto_detect': True,
            'auto_fix': True,
            'requires_approval': False
        }
    ]
    
    for error_data in default_errors:
        # 检查是否已存在
        existing = db.session.query(ErrorType).filter_by(code=error_data['code']).first()
        if not existing:
            error_type = ErrorType(**error_data)
            db.session.add(error_type)
    
    db.session.commit()


def init_default_ai_employees(db):
    """初始化默认的AI员工"""
    default_employees = [
        {
            'name': '代码修复专家',
            'employee_code': 'AI_FIXER_001',
            'description': '专门处理代码错误修复的AI员工',
            'capabilities': [
                '自动检测代码错误',
                '提供修复建议',
                '自动修复常见错误',
                '生成修复报告'
            ],
            'specialties': [
                'Python',
                'JavaScript',
                'Java',
                'C++'
            ],
            'status': AIEmployeeStatus.ACTIVE,
            'accuracy': 95.5,
            'model_version': '1.0.0'
        },
        {
            'name': '数学错误修复专家',
            'employee_code': 'AI_MATH_FIXER_001',
            'description': '专门处理数学相关错误的AI员工',
            'capabilities': [
                '检测数学运算错误',
                '修复除零错误',
                '处理复数运算',
                '验证数学公式'
            ],
            'specialties': [
                '线性代数',
                '微积分',
                '概率统计',
                '数值分析'
            ],
            'status': AIEmployeeStatus.ACTIVE,
            'accuracy': 98.2,
            'model_version': '1.0.0'
        },
        {
            'name': '异常处理专家',
            'employee_code': 'AI_EXC_FIXER_001',
            'description': '专门处理异常和错误的AI员工',
            'capabilities': [
                '识别异常类型',
                '提供异常处理建议',
                '优化异常捕获逻辑',
                '生成错误日志'
            ],
            'specialties': [
                '异常处理',
                '错误恢复',
                '日志记录',
                '调试技巧'
            ],
            'status': AIEmployeeStatus.ACTIVE,
            'accuracy': 92.8,
            'model_version': '1.0.0'
        },
        {
            'name': 'CDN和图标修复专家',
            'employee_code': 'AI_CDN_ICON_FIXER_001',
            'description': '专门修复CDN加载失败和图标显示问题的AI员工',
            'capabilities': [
                '检测CDN加载失败',
                '替换外部CDN为本地资源',
                '使用内联SVG替代字体图标',
                '优化资源加载策略',
                '缓存失效处理'
            ],
            'specialties': [
                'Font Awesome',
                'CDN优化',
                '图标系统',
                '前端资源管理',
                '性能优化'
            ],
            'status': AIEmployeeStatus.ACTIVE,
            'accuracy': 99.5,
            'model_version': '1.0.0'
        }
    ]
    
    for emp_data in default_employees:
        # 检查是否已存在
        existing = db.session.query(AIEmployee).filter_by(employee_code=emp_data['employee_code']).first()
        if not existing:
            employee = AIEmployee(**emp_data)
            db.session.add(employee)
    
    db.session.commit()
