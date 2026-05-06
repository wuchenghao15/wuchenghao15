# -*- coding: utf-8 -*-
import time
# JSON import removed - using database
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoginAnalyzerAI:
    """登录行为分析AI，负责分析用户登录行为、检测异常登录、提供安全建议"""

    def __init__(self):
        self.instance_id = f"login_analyzer_ai_{id(self)}"
        self.name = "登录行为分析AI"
        self.description = "负责分析用户登录行为、检测异常登录、提供安全建议"
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

            # 记录登录尝试
            login_time = datetime.now().isoformat()

            # 初始化用户登录历史
            if username not in self.login_history:
                self.login_history[username] = []

            # 添加当前登录尝试
            self.login_history[username].append({
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": login_time,
                "success": False
            })

            # 限制历史记录长度
            if len(self.login_history[username]) > 100:
                self.login_history[username] = self.login_history[username][-100:]

            # 分析登录模式
            analysis_result = {
                "username": username,
                "user_agent": user_agent,
                "is_anomaly": False,
                "risk_level": "low",
                "suggestions": [],
                "login_history_count": len(self.login_history[username])
            }

            # 检测异常登录
            if len(self.login_history[username]) > 1:
                analysis_result = self._detect_anomaly(analysis_result)

            # 生成安全建议
            analysis_result["suggestions"] = self._generate_suggestions(analysis_result)

            self.logger.info(f"登录尝试分析完成: {analysis_result}")
            return analysis_result

        except Exception as e:
            self.logger.error(f"分析登录尝试失败: {str(e)}")
            return {
                "username": username,
                "user_agent": user_agent,
                "timestamp": datetime.now().isoformat(),
                "anomaly_score": 0.0,
                "risk_level": "low",
                "suggestions": [],
                "login_history_count": 0

        """检测异常登录
            analysis_result: 分析结果
        Returns:
        """
        username = analysis_result["username"]
        user_agent = analysis_result["user_agent"]

        # 计算异常分数
        anomaly_score = 0.0

        # 检查IP地址变化
        recent_logins = self.login_history[username][-5:]
        ip_addresses = [login["ip_address"] for login in recent_logins[:-1]]
        if ip_address not in ip_addresses:
            anomaly_score += 0.3

        # 检查用户代理变化
        user_agents = [login["user_agent"] for login in recent_logins[:-1]]
        if user_agent not in user_agents:
            anomaly_score += 0.2

        # 检查登录频率
        login_times = [datetime.fromisoformat(login["timestamp"]) for login in recent_logins]
        time_diffs = [(login_times[i] - login_times[i+1]).total_seconds() for i in range(len(login_times)-1)]
        if time_diffs and min(time_diffs) < 60:  # 60秒内多次登录
            anomaly_score += 0.3

        # 检查登录时间
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # 凌晨或深夜登录
            anomaly_score += 0.2

        # 更新分析结果
        analysis_result["anomaly_score"] = anomaly_score

        if anomaly_score > self.anomaly_threshold:
            analysis_result["is_anomaly"] = True
        elif anomaly_score > self.anomaly_threshold * 0.5:
            analysis_result["is_anomaly"] = True
            analysis_result["risk_level"] = "medium"

        return analysis_result
    def _generate_suggestions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成安全建议

            analysis_result: 分析结果

        Returns:
            安全建议列表
        suggestions = []

                suggestions.append("建议检查账户活动，确保没有未授权访问")
            elif analysis_result["risk_level"] == "medium":
                suggestions.append("检测到可疑登录行为，建议验证登录设备")

        # 基于登录历史的建议
        login_count = analysis_result["login_history_count"]
            suggestions.append("登录次数较多，建议使用密码管理器")

        return suggestions

    def update_login_result(self, username: str, success: bool):
        """更新登录结果

            username: 用户名
            success: 是否成功
        """
            if username in self.login_history and self.login_history[username]:
                # 更新最近一次登录尝试的结果
                self.login_history[username][-1]["success"] = success
                self.logger.info(f"更新登录结果: {username}, 成功: {success}")
            self.logger.error(f"更新登录结果失败: {str(e)}")

    def get_login_statistics(self, username: str) -> Dict[str, Any]:

            username: 用户名

        Returns:
            登录统计信息
        try:
            if username not in self.login_history:
                return {
                    "total_logins": 0,
                    "successful_logins": 0,
                    "failed_logins": 0,
                    "last_login": None,
                }

            logins = self.login_history[username]
            total_logins = len(logins)
            failed_logins = total_logins - successful_logins

            last_login = logins[-1] if logins else None

            # 获取登录位置
            login_locations = list(set(login["ip_address"] for login in logins))

            return {
                "username": username,
                "total_logins": total_logins,
                "successful_logins": successful_logins,
                "failed_logins": failed_logins,
                "last_login": last_login,
                "login_locations": login_locations
            }
        except Exception as e:
            self.logger.error(f"获取登录统计信息失败: {str(e)}")
            return {
                "username": username,
                "total_logins": 0,
                "successful_logins": 0,
                "failed_logins": 0,
                "last_login": None,
                "login_locations": []
            }

    def __str__(self):
        return f"LoginAnalyzerAI(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()

# 创建全局登录行为分析AI实例
ai_login_analyzer = LoginAnalyzerAI()
