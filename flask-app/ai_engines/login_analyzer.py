# -*- coding: utf-8 -*-
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoginAnalyzerAI:
    """登录行为分析AI: 负责分析用户登录行为,检测异常登录,提供安全建议"""

    def __init__(self):
        self.instance_id = f"login_analyzer_ai_{id(self)}"
        self.name = "登录行为分析AI"
        self.description = "负责分析用户登录行为,检测异常登录,提供安全建议"
        self.logger = logger
        self.logger.info(f"初始化登录行为分析AI: {self.instance_id}")
        self.login_history = {}
        self.anomaly_threshold = 0.7

    def analyze_login_attempt(self, username: str, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """分析登录尝试

        Args:
            username: 用户名
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            分析结果
        """
        try:
            self.logger.info(f"分析登录尝试: {username}, IP: {ip_address}, User-Agent: {user_agent}")

            login_time = datetime.now().isoformat()

            if username not in self.login_history:
                self.login_history[username] = []

            self.login_history[username].append({
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": login_time,
                "success": False
            })

            if len(self.login_history[username]) > 100:
                self.login_history[username] = self.login_history[username][-100:]

            analysis_result = {
                "username": username,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "is_anomaly": False,
                "risk_level": "low",
                "suggestions": [],
                "login_history_count": len(self.login_history[username])
            }

            if len(self.login_history[username]) > 1:
                analysis_result = self._detect_anomaly(analysis_result)

            analysis_result["suggestions"] = self._generate_suggestions(analysis_result)

            self.logger.info(f"登录尝试分析完成: {analysis_result}")
            return analysis_result
        except Exception as e:
            self.logger.error(f"分析登录尝试失败: {str(e)}")
            return {"error": str(e)}

    def _detect_anomaly(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """检测异常登录"""
        username = analysis_result["username"]
        history = self.login_history.get(username, [])

        if len(history) < 2:
            return analysis_result

        current_ip = analysis_result["ip_address"]
        previous_ips = [h["ip_address"] for h in history[:-1]]

        if current_ip not in previous_ips:
            analysis_result["is_anomaly"] = True
            analysis_result["risk_level"] = "medium"
            analysis_result["anomaly_type"] = "new_ip"

        return analysis_result

    def _generate_suggestions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成安全建议"""
        suggestions = []

        if analysis_result.get("is_anomaly"):
            suggestions.append("检测到异常登录,建议启用两步验证")

        if analysis_result.get("risk_level") == "high":
            suggestions.append("高风险登录,建议立即修改密码")

        return suggestions

    def update_login_result(self, username: str, success: bool):
        """更新登录结果

        Args:
            username: 用户名
            success: 是否成功
        """
        try:
            if username in self.login_history and self.login_history[username]:
                self.login_history[username][-1]["success"] = success
                self.logger.info(f"更新登录结果: {username}, 成功: {success}")
        except Exception as e:
            self.logger.error(f"更新登录结果失败: {str(e)}")

    def get_login_statistics(self, username: str) -> Dict[str, Any]:
        """获取登录统计信息

        Args:
            username: 用户名

        Returns:
            登录统计信息
        """
        try:
            if username not in self.login_history:
                return {"total_logins": 0}

            history = self.login_history[username]
            total_logins = len(history)
            successful_logins = sum(1 for h in history if h.get("success"))

            return {
                "total_logins": total_logins,
                "successful_logins": successful_logins,
                "failed_logins": total_logins - successful_logins,
                "success_rate": successful_logins / total_logins if total_logins > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"获取登录统计失败: {str(e)}")
            return {}

    def __str__(self):
        return f"LoginAnalyzerAI(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()
