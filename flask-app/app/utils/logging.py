import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from app.config import Config
import threading


class ContextFilter(logging.Filter):
    """
    日志上下文过滤器，用于添加额外的上下文信息
    """
    
    def __init__(self):
        super().__init__()
        self._context = threading.local()
    
    def set_context(self, **kwargs):
        """
        设置上下文信息
        
        Args:
            **kwargs: 上下文键值对
        """
        for key, value in kwargs.items():
            setattr(self._context, key, value)
    
    def clear_context(self):
        """
        清除上下文信息
        """
        self._context.__dict__.clear()
    
    def filter(self, record):
        """
        过滤日志记录，添加上下文信息
        
        Args:
            record: 日志记录对象
            
        Returns:
            bool: 是否通过过滤
        """
        # 添加上下文信息到日志记录
        for key, value in self._context.__dict__.items():
            setattr(record, key, value)
        
        # 确保所有日志记录都有基本信息
        if not hasattr(record, 'request_id'):
            record.request_id = getattr(self._context, 'request_id', 'N/A')
        if not hasattr(record, 'client_ip'):
            record.client_ip = getattr(self._context, 'client_ip', 'N/A')
        if not hasattr(record, 'user_id'):
            record.user_id = getattr(self._context, 'user_id', 'N/A')
        
        return True


class LoggingManager:
    """
    日志管理器，用于统一管理日志系统
    """
    
    def __init__(self):
        self._loggers = {}
        self._context_filter = ContextFilter()
        self._log_stats = {
            'debug': 0,
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0
        }
        self._lock = threading.Lock()
    
    def configure_logging(self):
        """
        配置日志系统
        """
        # 创建格式化器，添加上下文信息支持
        context_format = ('%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d ' \
                        '- request_id=%(request_id)s - client_ip=%(client_ip)s - user_id=%(user_id)s - %(message)s')
        formatter = logging.Formatter(context_format)
        
        # 创建控制台格式化器，中文显示客户端交互信息
        console_format = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')
        
        # 创建文件处理器 - 大小轮转 (10MB, 最多保留10个备份)
        size_handler = RotatingFileHandler(
            Config.LOG_SIZE_FILE,
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8',
            delay=True  # 延迟创建文件，直到有日志写入
        )
        size_handler.setFormatter(formatter)
        size_handler.addFilter(self._context_filter)
        
        # 创建文件处理器 - 时间轮转 (每天轮转, 最多保留30天)
        time_handler = TimedRotatingFileHandler(
            Config.LOG_TIME_FILE,
            when=Config.LOG_ROTATE_WHEN,
            interval=Config.LOG_ROTATE_INTERVAL,
            backupCount=Config.LOG_ROTATE_BACKUP_COUNT,
            encoding='utf-8',
            delay=True  # 延迟创建文件，直到有日志写入
        )
        time_handler.setFormatter(formatter)
        time_handler.addFilter(self._context_filter)
        
        # 创建控制台处理器，简化格式以提高性能
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(self._context_filter)
        
        # 获取根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # 根日志器设置为DEBUG级别
        
        # 清除默认处理器
        root_logger.handlers.clear()
        
        # 添加自定义处理器
        root_logger.addHandler(size_handler)
        root_logger.addHandler(time_handler)
        root_logger.addHandler(console_handler)
        
        # 设置特定模块的日志级别，确保werkzeug记录详细的客户端交互信息
        self.set_module_log_level('werkzeug', logging.DEBUG)
        self.set_module_log_level('sqlite3', logging.ERROR)
        self.set_module_log_level('flask', logging.DEBUG)
        self.set_module_log_level('sqlalchemy', logging.ERROR)
        
        # 创建并配置主日志记录器
        main_logger = self.get_logger('MTSCOS_AI_Project')
        main_logger.setLevel(Config.LOG_LEVEL)
        
        main_logger.info("日志系统配置完成")
        return main_logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器对象
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.addFilter(self._context_filter)
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def set_module_log_level(self, module_name: str, level: int):
        """
        设置特定模块的日志级别
        
        Args:
            module_name: 模块名称
            level: 日志级别
        """
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
        
        self.get_logger('MTSCOS_AI_Project').info(f"设置模块 {module_name} 的日志级别为 {logging.getLevelName(level)}")
    
    def set_global_log_level(self, level: int):
        """
        设置全局日志级别
        
        Args:
            level: 日志级别
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        self.get_logger('MTSCOS_AI_Project').info(f"设置全局日志级别为 {logging.getLevelName(level)}")
    
    def get_log_stats(self) -> Dict[str, int]:
        """
        获取日志统计信息
        
        Returns:
            Dict[str, int]: 日志统计字典
        """
        with self._lock:
            return self._log_stats.copy()
    
    def increment_log_count(self, level: str):
        """
        增加日志计数
        
        Args:
            level: 日志级别
        """
        level = level.lower()
        with self._lock:
            if level in self._log_stats:
                self._log_stats[level] += 1
            else:
                self._log_stats[level] = 1
    
    def get_context_filter(self) -> ContextFilter:
        """
        获取上下文过滤器
        
        Returns:
            ContextFilter: 上下文过滤器对象
        """
        return self._context_filter
    
    def set_context(self, **kwargs):
        """
        设置上下文信息
        
        Args:
            **kwargs: 上下文键值对
        """
        self._context_filter.set_context(**kwargs)
    
    def clear_context(self):
        """
        清除上下文信息
        """
        self._context_filter.clear_context()


# 创建立即日志记录器的子类，用于统计日志数量
class CountingLogger(logging.Logger):
    """
    带计数功能的日志记录器
    """
    
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        self._logging_manager = None
    
    def set_logging_manager(self, manager: LoggingManager):
        """
        设置日志管理器
        
        Args:
            manager: 日志管理器对象
        """
        self._logging_manager = manager
    
    def log(self, level, msg, *args, **kwargs):
        """
        记录日志并统计数量
        """
        super().log(level, msg, *args, **kwargs)
        
        if self._logging_manager:
            level_name = logging.getLevelName(level).lower()
            self._logging_manager.increment_log_count(level_name)


# 将Logger类替换为CountingLogger
logging.setLoggerClass(CountingLogger)

# 创建全局日志管理器实例
logging_manager = LoggingManager()

# 配置日志系统并获取主日志记录器
logger = logging_manager.configure_logging()

# 设置日志管理器引用
for logger_name, logger_instance in logging_manager._loggers.items():
    if isinstance(logger_instance, CountingLogger):
        logger_instance.set_logging_manager(logging_manager)

