import re
import time
import logging
from app.utils.logging import logger
from app.config import Config

class LogAnalyzerAI:
    """日志分析AI，负责日志分析和异常检测"""
    
    def __init__(self):
        self.instance_id = f"log_analyzer_ai_{id(self)}"
        self.name = "日志分析AI"
        self.description = "负责日志分析和异常检测"
        self.logger = logger
        self.logger.info(f"初始化日志分析AI: {self.instance_id}")
        
        # 日志模式正则表达式
        self.log_patterns = {
            "error": r"(?i)error|exception|fail|critical",
            "warning": r"(?i)warning|warn",
            "info": r"(?i)info|notice",
            "debug": r"(?i)debug|trace"
        }
        
        # 异常关键词
        self.error_keywords = [
            "TypeError", "AttributeError", "NameError", "ValueError",
            "IndexError", "KeyError", "FileNotFoundError", "PermissionError",
            "ConnectionError", "TimeoutError", "ImportError", "ModuleNotFoundError"
        ]
    
    def analyze_logs(self, log_content, time_range=None):
        """分析日志内容"""
        try:
            self.logger.info(f"{self.instance_id} 正在分析日志")
            
            log_lines = log_content.splitlines()
            analysis_result = {
                "total_lines": len(log_lines),
                "level_counts": {
                    "error": 0,
                    "warning": 0,
                    "info": 0,
                    "debug": 0
                },
                "errors": [],
                "warnings": [],
                "anomalies": [],
                "top_error_types": {},
                "timeline": []
            }
            
            # 逐行分析日志
            for line in log_lines:
                if not line.strip():
                    continue
                
                # 分析日志级别
                log_level = self._detect_log_level(line)
                if log_level:
                    analysis_result["level_counts"][log_level] += 1
                
                # 分析错误和警告
                if log_level == "error":
                    error_info = self._extract_error_info(line)
                    analysis_result["errors"].append(error_info)
                    
                    # 统计错误类型
                    error_type = error_info.get("type", "unknown")
                    analysis_result["top_error_types"][error_type] = analysis_result["top_error_types"].get(error_type, 0) + 1
                elif log_level == "warning":
                    warning_info = self._extract_warning_info(line)
                    analysis_result["warnings"].append(warning_info)
                
                # 检测异常
                anomaly = self._detect_anomaly(line)
                if anomaly:
                    analysis_result["anomalies"].append(anomaly)
                
                # 构建时间线
                time_info = self._extract_time_info(line)
                if time_info:
                    analysis_result["timeline"].append({
                        "time": time_info,
                        "level": log_level,
                        "message": line
                    })
            
            # 排序时间线
            analysis_result["timeline"].sort(key=lambda x: x["time"])
            
            # 生成告警
            alerts = self._generate_alerts(analysis_result)
            analysis_result["alerts"] = alerts
            
            self.logger.info(f"{self.instance_id} 日志分析完成")
            return analysis_result
        except Exception as e:
            self.logger.error(f"{self.instance_id} 日志分析失败: {str(e)}")
            return None
    
    def detect_anomalies(self, log_entries):
        """检测日志中的异常"""
        try:
            self.logger.info(f"{self.instance_id} 正在检测日志异常")
            
            anomalies = []
            
            for entry in log_entries:
                if isinstance(entry, dict):
                    message = entry.get("message", "")
                    timestamp = entry.get("timestamp", time.time())
                else:
                    message = entry
                    timestamp = time.time()
                
                anomaly = self._detect_anomaly(message)
                if anomaly:
                    anomalies.append({
                        "timestamp": timestamp,
                        "message": message,
                        "anomaly_type": anomaly["type"],
                        "description": anomaly["description"]
                    })
            
            self.logger.info(f"{self.instance_id} 异常检测完成，发现 {len(anomalies)} 个异常")
            return anomalies
        except Exception as e:
            self.logger.error(f"{self.instance_id} 异常检测失败: {str(e)}")
            return []
    
    def generate_alerts(self, analysis_result):
        """基于分析结果生成告警"""
        try:
            self.logger.info(f"{self.instance_id} 正在生成告警")
            
            alerts = []
            
            # 错误数量告警
            error_count = analysis_result["level_counts"]["error"]
            if error_count > 10:
                alerts.append({
                    "level": "critical",
                    "message": f"发现 {error_count} 个错误，需要立即处理",
                    "timestamp": time.time()
                })
            elif error_count > 5:
                alerts.append({
                    "level": "warning",
                    "message": f"发现 {error_count} 个错误，建议检查",
                    "timestamp": time.time()
                })
            
            # 异常告警
            anomaly_count = len(analysis_result["anomalies"])
            if anomaly_count > 5:
                alerts.append({
                    "level": "warning",
                    "message": f"发现 {anomaly_count} 个异常，建议检查",
                    "timestamp": time.time()
                })
            
            # 特定错误类型告警
            for error_type, count in analysis_result["top_error_types"].items():
                if count > 3 and error_type != "unknown":
                    alerts.append({
                        "level": "warning",
                        "message": f"频繁出现 {error_type} 错误，共 {count} 次",
                        "timestamp": time.time()
                    })
            
            self.logger.info(f"{self.instance_id} 生成了 {len(alerts)} 个告警")
            return alerts
        except Exception as e:
            self.logger.error(f"{self.instance_id} 告警生成失败: {str(e)}")
            return []
    
    def _detect_log_level(self, log_line):
        """检测日志级别"""
        for level, pattern in self.log_patterns.items():
            if re.search(pattern, log_line, re.IGNORECASE):
                return level
        return None
    
    def _extract_error_info(self, log_line):
        """提取错误信息"""
        error_info = {
            "message": log_line,
            "type": "unknown"
        }
        
        # 提取错误类型
        for keyword in self.error_keywords:
            if keyword in log_line:
                error_info["type"] = keyword
                break
        
        return error_info
    
    def _extract_warning_info(self, log_line):
        """提取警告信息"""
        return {
            "message": log_line
        }
    
    def _detect_anomaly(self, log_line):
        """检测日志中的异常"""
        # 检测异常关键词
        for keyword in self.error_keywords:
            if keyword in log_line:
                return {
                    "type": "exception",
                    "description": f"发现异常: {keyword}",
                    "message": log_line
                }
        
        # 检测重复错误模式
        if re.search(r"(\[.*\])\s+ERROR\s+.*\1", log_line):
            return {
                "type": "repeated_error",
                "description": "发现重复错误模式",
                "message": log_line
            }
        
        # 检测超时或连接错误
        if re.search(r"(?i)timeout|connection|failed to connect", log_line):
            return {
                "type": "connection_error",
                "description": "发现连接或超时错误",
                "message": log_line
            }
        
        # 检测权限错误
        if re.search(r"(?i)permission|denied|access", log_line):
            return {
                "type": "permission_error",
                "description": "发现权限错误",
                "message": log_line
            }
        
        return None
    
    def _extract_time_info(self, log_line):
        """提取时间信息"""
        # 匹配常见的日志时间格式
        time_patterns = [
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",  # YYYY-MM-DD HH:MM:SS
            r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}",  # MM/DD/YYYY HH:MM:SS
            r"\d{2}:\d{2}:\d{2}",  # HH:MM:SS
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?"  # ISO格式
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, log_line)
            if match:
                return match.group(0)
        
        return None
    
    def _generate_alerts(self, analysis_result):
        """生成告警"""
        alerts = []
        
        # 基于错误数量生成告警
        error_count = analysis_result["level_counts"]["error"]
        if error_count > 5:
            alerts.append({
                "level": "critical" if error_count > 10 else "warning",
                "message": f"检测到 {error_count} 个错误",
                "details": analysis_result["top_error_types"]
            })
        
        # 基于警告数量生成告警
        warning_count = analysis_result["level_counts"]["warning"]
        if warning_count > 10:
            alerts.append({
                "level": "warning",
                "message": f"检测到 {warning_count} 个警告"
            })
        
        # 基于异常生成告警
        anomaly_count = len(analysis_result["anomalies"])
        if anomaly_count > 3:
            alerts.append({
                "level": "warning",
                "message": f"检测到 {anomaly_count} 个异常"
            })
        
        return alerts
    
    def get_log_summary(self, log_content):
        """获取日志摘要"""
        analysis = self.analyze_logs(log_content)
        if not analysis:
            return None
        
        summary = {
            "total_lines": analysis["total_lines"],
            "error_count": analysis["level_counts"]["error"],
            "warning_count": analysis["level_counts"]["warning"],
            "top_error_types": dict(sorted(analysis["top_error_types"].items(), key=lambda x: x[1], reverse=True)[:5]),
            "alert_count": len(analysis.get("alerts", []))
        }
        
        return summary
    
    def __str__(self):
        return f"LogAnalyzerAI(instance_id={self.instance_id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()

# 创建全局日志分析AI实例
log_analyzer_ai = LogAnalyzerAI()