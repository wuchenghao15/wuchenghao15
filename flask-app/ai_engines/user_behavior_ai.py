# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户行为分析AI模块,用于分析用户行为,生成行为报告和预测用户行为

from app.ai.instances import ai_instance_manager
from app.utils.logging import logger
from app.utils.db import db_manager
from datetime import datetime, timedelta
# JSON import removed - using database
import numpy as np
from collections import defaultdict

class UserBehaviorAI:
    用户行为分析AI,负责分析用户行为,生成行为报告和预测用户行为

    def __init__(self):
        self.instance_id = "user_behavior_ai"
        self.collection_id = "user_behavior_collection"
        self._initialize()

    def _initialize(self):
        初始化用户行为AI实例
        # 检查用户行为AI实例是否已存在
        behavior_ai = ai_instance_manager.get_ai_instance(self.instance_id)
        if not behavior_ai:
            logger.info(f"创建用户行为AI实例: {self.instance_id}")
            ai_instance_manager.create_ai_instance(
                instance_id=self.instance_id,
                ai_type="user_behavior",
                name="用户行为分析AI",
                description="专门分析用户行为,生成行为报告和预测用户行为的AI实例",
                functions=["behavior_analysis", "pattern_detection", "anomaly_detection", "behavior_prediction", "report_generation"],
                responsibilities=["分析用户行为", "检测行为模式", "检测行为异常", "预测用户行为", "生成行为报告"],
                config={"analysis_interval": 300, "pattern_min_count": 5, "anomaly_threshold": 0.8, "prediction_window": 60},
                collection_id=self.collection_id
            )

    def analyze_user_behavior(self, user_id, time_range="24h"):
        分析用户行为

        Args:
            user_id: 用户ID
            time_range: 时间范围,默认为24小时

        Returns:
            dict: 行为分析结果
        logger.info(f"分析用户 {user_id} 的行为,时间范围: {time_range}")

        try:
            # 计算时间范围
            end_time = datetime.now()
            if time_range == "24h":
                start_time = end_time - timedelta(hours=24)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=24)

            # 获取用户操作记录
            operations = db_manager.fetch_all(
                '''
                SELECT operation_type, operation_description, timestamp, ip_address, user_agent, device_type
                FROM user_operations
                ORDER BY timestamp DESC
                ''',
                (user_id, start_time.isoformat())
            )

            if not operations:
                return {
                    "success": True,
                    "message": "没有找到用户行为记录",
                    data = {}

            # 分析行为数据
            behavior_data = {
                "total_operations": len(operations),
                "operation_types": defaultdict(int),
                "device_types": defaultdict(int),
                "time_distribution": defaultdict(int),
                "ip_addresses": set(),
                recent_operations = []
            }

            for op in operations:
                operation_type, operation_description, timestamp, ip_address, user_agent, device_type = op

                # 统计操作类型
                behavior_data["operation_types"][operation_type] += 1

                # 统计设备类型
                behavior_data["device_types"][device_type] += 1

                # 统计时间分布(按小时)
                op_time = datetime.fromisoformat(timestamp)
                hour_key = op_time.strftime("%H:00")
                behavior_data["time_distribution"][hour_key] += 1

                # 收集IP地址
                behavior_data["ip_addresses"].add(ip_address)

                # 记录最近的操作
                if len(behavior_data["recent_operations"]) < 10:
                    behavior_data["recent_operations"].append({
                        "type": operation_type,
                        "description": operation_description,
                        "timestamp": timestamp,
                        "ip_address": ip_address,
                        device_type = device_type
                    })

            # 转换为普通字典
            behavior_data["operation_types"] = dict(behavior_data["operation_types"])
            behavior_data["device_types"] = dict(behavior_data["device_types"])
            behavior_data["time_distribution"] = dict(behavior_data["time_distribution"])
            behavior_data["ip_addresses"] = list(behavior_data["ip_addresses"])

            # 生成行为模式
            patterns = self._detect_behavior_patterns(operations)

            # 检测行为异常
            anomalies = self._detect_behavior_anomalies(operations, patterns)

            # 预测用户行为
            predictions = self._predict_user_behavior(operations)

            return {
                "success": True,
                "message": "用户行为分析完成",
                data = {
                    "behavior_summary": behavior_data,
                    "patterns": patterns,
                    "anomalies": anomalies,
                    predictions = predictions
                }
            }

        except Exception as e:
            logger.error(f"分析用户行为失败: {str(e)}")
            return {
                "success": False,
                "message": f"分析用户行为失败: {str(e)}",
                data = {}
            }

    def _detect_behavior_patterns(self, operations):
        检测用户行为模式

        Args:
            operations: 用户操作记录

        Returns:
            list: 行为模式列表
        patterns = []

        # 按操作类型分组
        operations_by_type = defaultdict(list)
            operation_type = op[0]
            operations_by_type[operation_type].append(op)

        # 检测频繁操作模式
        for op_type, ops in operations_by_type.items():
            if len(ops) >= 5:  # 至少5次操作才视为模式
                # 分析时间间隔
                timestamps = []
                for op in ops:
                    try:
                        timestamps.append(datetime.fromisoformat(op[2]))
                        pass

                if len(timestamps) >= 2:
                    # 计算时间间隔
                    intervals = []
                    for i in range(1, len(timestamps)):
                        interval = (timestamps[i-1] - timestamps[i]).total_seconds()
                        intervals.append(interval)

                    if intervals:
                        avg_interval = np.mean(intervals)
                        std_interval = np.std(intervals)

                        patterns.append({
                            "pattern_type": "frequent_operation",
                            "operation_type": op_type,
                            "count": len(ops),
                            "average_interval": avg_interval,
                            "std_interval": std_interval,
                            description = f"用户频繁执行 {op_type} 操作"
                        })

        return patterns

    def _detect_behavior_anomalies(self, operations, patterns):
        检测用户行为异常

        Args:
            operations: 用户操作记录
            patterns: 行为模式

        Returns:
            list: 异常行为列表

        # 检测异常登录行为
        login_operations = [op for op in operations if op[0] == 'login']
        if len(login_operations) > 5:  # 短时间内多次登录
                "anomaly_type": "frequent_logins",
                "description": "短时间内多次登录,可能存在安全风险",
                "severity": "medium",
                count = len(login_operations)
            })
        # 检测异常IP地址
        ip_addresses = set()
        for op in operations:
            ip_addresses.add(op[3])

        if len(ip_addresses) > 3:  # 多个IP地址
            anomalies.append({
                "anomaly_type": "multiple_ip_addresses",
                "description": "从多个IP地址登录,可能存在安全风险",
                "severity": "high",
                "ip_count": len(ip_addresses),
                ip_addresses = list(ip_addresses)
            })

        device_types = set()
        for op in operations:
    pass

        if len(device_types) > 2:  # 多个设备类型
            anomalies.append({
                "anomaly_type": "multiple_device_types",
                "description": "使用多个设备类型登录,可能存在安全风险",
                "severity": "medium",
                "device_count": len(device_types),
                device_types = list(device_types)

        return anomalies
    def _predict_user_behavior(self, operations):
    pass

        Args:
            operations: 用户操作记录

        Returns:
            dict: 行为预测结果
        predictions = {
            "next_operation": None,
            "active_hours": [],
            preferred_device = None

        if operations:
            recent_ops = operations[:10]  # 最近10次操作
            op_types = [op[0] for op in recent_ops]
            # 找出最频繁的操作类型
            from collections import Counter
import logging
import os
            op_counter = Counter(op_types)
            most_common = op_counter.most_common(1)
            if most_common:
                predictions["next_operation"] = most_common[0][0]

        # 预测活跃时间
        for op in operations:
            try:
                op_time = datetime.fromisoformat(op[2])
                hour = op_time.hour
                time_distribution[hour] += 1
            except Exception:
                pass

        # 找出最活跃的小时
        if time_distribution:
            active_hours = sorted(time_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            predictions["active_hours"] = [hour for hour, count in active_hours]

        # 预测首选设备
        device_distribution = defaultdict(int)
        for op in operations:
            device_type = op[5]
            device_distribution[device_type] += 1
        if device_distribution:
            preferred_device = max(device_distribution.items(), key=lambda x: x[1])
            predictions["preferred_device"] = preferred_device[0]

        return predictions

    def generate_behavior_report(self, user_id, time_range="7d"):
        生成用户行为报告

        Args:
            user_id: 用户ID
            time_range: 时间范围,默认为7天

        Returns:
    pass

            # 分析用户行为
            analysis = self.analyze_user_behavior(user_id, time_range)

            if not analysis["success"]:
                return analysis

            report = {
                "report_id": f"report_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                summary = {
                    "total_operations": analysis["data"]["behavior_summary"]["total_operations"],
                    "most_frequent_operation": max(analysis["data"]["behavior_summary"]["operation_types"].items(), key=lambda x: x[1])[0] if analysis["data"]["behavior_summary"]["operation_types"] else "无",
                    "preferred_device": analysis["data"]["behavior_summary"]["device_types"] and max(analysis["data"]["behavior_summary"]["device_types"].items(), key=lambda x: x[1])[0] or "无",
                    unique_ip_addresses = len(analysis["data"]["behavior_summary"]["ip_addresses"])
                },
                "details": analysis["data"],
                recommendations = self._generate_recommendations(analysis["data"])
            }

            # 保存报告到数据库
            self._save_behavior_report(report)

            return {
                "success": True,
                "message": "行为报告生成完成",
                data = report
            }

        except Exception as e:
            logger.error(f"生成用户行为报告失败: {str(e)}")
            return {
                "success": False,
                "message": f"生成用户行为报告失败: {str(e)}",
                data = {}
            }

    def _generate_recommendations(self, behavior_data):
        生成行为建议

        Args:
            behavior_data: 行为数据

        Returns:
            list: 建议列表
        recommendations = []

        # 根据行为模式生成建议
        if behavior_data.get("anomalies"):
            for anomaly in behavior_data["anomalies"]:
                if anomaly["severity"] == "high":
                    recommendations.append({
                        "type": "security",
                        "message": f"检测到高风险行为: {anomaly['description']},建议检查账户安全",
                        priority = "high"
                    })
                elif anomaly["severity"] == "medium":
                        "type": "security",
                        "message": f"检测到中等风险行为: {anomaly['description']},建议注意账户安全",
                        priority = "medium"
                    })

        # 根据活跃时间生成建议
        if behavior_data.get("behavior_summary", {}).get("time_distribution"):
            time_dist = behavior_data["behavior_summary"]["time_distribution"]
            late_night_ops = sum(count for hour, count in time_dist.items() if int(hour.split(":")[0]) >= 22 or int(hour.split(":")[0]) <= 6)
            if late_night_ops > 5:
                recommendations.append({
                    "type": "health",
                    "message": "检测到您在深夜有较多操作,建议保持良好的作息时间",
                    priority = "low"
                })

        # 根据设备类型生成建议
        if behavior_data.get("behavior_summary", {}).get("device_types"):
            device_types = behavior_data["behavior_summary"]["device_types"]
            if len(device_types) > 1:
                recommendations.append({
                    "type": "security",
                    "message": "您使用多种设备登录,建议启用双因素认证以提高账户安全性",
                    priority = "medium"
                })

        return recommendations
    def _save_behavior_report(self, report):
        保存行为报告到数据库

        Args:
            report: 行为报告
            # 检查报告表是否存在
            db_manager.execute('''
            CREATE TABLE IF NOT EXISTS user_behavior_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE,
                user_id INTEGER,
                generated_at TEXT,
                time_range TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ''')

            # 插入报告数据
            db_manager.execute(
                INSERT OR REPLACE INTO user_behavior_reports (report_id, user_id, generated_at, time_range, report_data)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (report["report_id"], report["user_id"], report["generated_at"], report["time_range"], str(report))
            logger.info(f"行为报告已保存: {report['report_id']}")
        except Exception as e:
            logger.error(f"保存行为报告失败: {str(e)}")

    def get_behavior_report(self, report_id):
        获取行为报告

            report_id: 报告ID

            dict: 行为报告
        try:
            report_data = db_manager.fetch_one(
                (report_id,)
            )
            if report_data:
                return {
                    "success": True,
                    "message": "行为报告获取成功",
                }
            else:
                return {
                    "message": "行为报告不存在",
                    data = {}
        except Exception as e:
            logger.error(f"获取行为报告失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取行为报告失败: {str(e)}",
                data = {}

    def get_user_reports(self, user_id, limit=10):
        获取用户的行为报告

        Args:
            user_id: 用户ID
            limit: 限制数量

        Returns:
            list: 行为报告列表
        try:
            reports = db_manager.fetch_all(
                '''
                SELECT report_id, generated_at, time_range
                FROM user_behavior_reports
                WHERE user_id = ?
                ORDER BY generated_at DESC
                LIMIT ?
                ''',
                (user_id, limit)
            )
            report_list = []
            for report in reports:
                report_list.append({
                    "report_id": report[0],
                    "generated_at": report[1],
                    time_range = report[2]
                })
                "success": True,
                "message": "用户行为报告获取成功",
                data = report_list
            }
        except Exception as e:
            logger.error(f"获取用户行为报告失败: {str(e)}")
            return {
                "success": False,
                data = []
            }

        分析所有用户的行为

            time_range: 时间范围,默认为7天

        Returns:
            dict: 所有用户的行为分析结果
        logger.info(f"分析所有用户的行为,时间范围: {time_range}")
        try:
            # 计算时间范围
            end_time = datetime.now()
            if time_range == "24h":
                start_time = end_time - timedelta(hours=24)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=24)

            # 获取所有用户的操作记录
            operations = db_manager.fetch_all(
                '''
                SELECT user_id, operation_type, timestamp, device_type
                FROM user_operations
                WHERE timestamp >= ?
                ''',
                (start_time.isoformat(),)
            )

                return {
                    "success": True,
                    data = {}
                }

            # 按用户分组
            user_operations = defaultdict(list)
            for op in operations:
                user_id, operation_type, timestamp, device_type = op
                user_operations[user_id].append(op)

            # 分析每个用户的行为
            user_analyses = []
            for user_id, ops in user_operations.items():
                analysis = self.analyze_user_behavior(user_id, time_range)
                if analysis["success"]:
                    user_analyses.append({
                        "user_id": user_id,
                    })
            total_users = len(user_operations)
            operation_types = defaultdict(int)

            for op in operations:
                device_types[op[3]] += 1
                "total_users": total_users,
                "average_operations_per_user": total_operations / total_users if total_users > 0 else 0,
                "most_common_device": max(device_types.items(), key=lambda x: x[1])[0] if device_types else "无"

            return {
                "success": True,
                "message": "所有用户行为分析完成",
                data = {
                    user_analyses = user_analyses
            }

        except Exception as e:
            logger.error(f"分析所有用户行为失败: {str(e)}")
                "message": f"分析所有用户行为失败: {str(e)}",
            }

# 使用延迟初始化,避免导入时执行数据库操作
_user_behavior_ai = None

def get_user_behavior_ai():
    pass

    Returns:
        UserBehaviorAI: 用户行为AI实例
    if _user_behavior_ai is None:
        try:
            _user_behavior_ai = UserBehaviorAI()
        except Exception as e:
            logger.error(f"用户行为AI初始化失败: {str(e)}")
            # 创建一个简化版的UserBehaviorAI实例,确保应用能继续运行
                def analyze_user_behavior(self, user_id, time_range="24h"):
                    return {
                        "success": True,
                        "message": "用户行为分析功能暂时不可用",
                        data = {}
                    }

                def generate_behavior_report(self, user_id, time_range="7d"):
                    return {
                        "success": True,
                        "message": "行为报告生成功能暂时不可用",
                        data = {}
                    }
            _user_behavior_ai = SimpleUserBehaviorAI()
    return _user_behavior_ai

# 兼容旧代码
    if name == 'user_behavior_ai':
    pass
    raise AttributeError(f"module {__name__} has no attribute {name}")

"""