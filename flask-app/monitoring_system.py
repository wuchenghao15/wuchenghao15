# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控系统
用于监控AI员工系统、分布式系统和影子系统
"""

import time
import uuid
import logging
import threading
import json
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MonitoringSystem')

class MetricType(Enum):
    """指标类型枚举"""
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MonitoringSystem:
    """监控系统"""

    def __init__(self, system_id):
        """初始化监控系统"""
        self.system_id = system_id or f"monitor_{uuid.uuid4().hex[:8]}"
        self.is_running = False
        self.metrics = defaultdict(list)
        self.alerts = []
        self.alert_rules = []
        self.monitored_systems = {}
        self.metric_queue = deque()
        self.config = {
            "metric_retention": 3600,
            "alert_check_interval": 10,
            "max_metrics_per_type": 1000,
            "max_alerts": 1000,
            "max_queue_size": 10000
        }
        self.lock = threading.Lock()
        self.monitoring_thread = None
        self.alert_thread = None

        logger.info(f"初始化监控系统: {self.system_id}")

    def start(self):
        """启动监控系统"""
        if self.is_running:
            logger.warning(f"监控系统 {self.system_id} 已在运行")
            return

        self.is_running = True

        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        self.alert_thread = threading.Thread(target=self._alert_loop)
        self.alert_thread.daemon = True
        self.alert_thread.start()

        logger.info(f"监控系统已启动: {self.system_id}")

    def stop(self):
        """停止监控系统"""
        if not self.is_running:
            logger.warning(f"监控系统 {self.system_id} 未在运行")
            return

        self.is_running = False

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        if self.alert_thread:
            self.alert_thread.join(timeout=5)

        logger.info(f"监控系统已停止: {self.system_id}")

    def register_system(self, system_id, system_type, system_instance=None):
        """注册被监控系统"""
        with self.lock:
            if system_id in self.monitored_systems:
                logger.warning(f"系统已注册: {system_id}")
                return False

            self.monitored_systems[system_id] = {
                "system_id": system_id,
                "type": system_type,
                "instance": system_instance,
                "status": "active",
                "last_check": time.time(),
                "metrics": []
            }

            logger.info(f"系统已注册: {system_id}")
            return True

    def unregister_system(self, system_id):
        """注销被监控系统"""
        with self.lock:
            if system_id in self.monitored_systems:
                del self.monitored_systems[system_id]
                logger.info(f"系统已注销: {system_id}")
                return True
            return False

    def add_metric(self, system_id, metric_name, value, metric_type=MetricType.GAUGE, tags=None):
        """添加指标"""
        if not self.is_running:
            return

        metric = {
            "system_id": system_id,
            "name": metric_name,
            "value": value,
            "type": metric_type.value,
            "tags": tags or {},
            "timestamp": time.time()
        }

        self.metric_queue.append(metric)

        if len(self.metric_queue) > self.config["max_queue_size"]:
            self.metric_queue.popleft()

    def add_alert_rule(self, rule_id, metric_name, condition, threshold, alert_level, description=None):
        """添加告警规则"""
        rule = {
            "rule_id": rule_id,
            "metric_name": metric_name,
            "condition": condition,
            "threshold": threshold,
            "level": alert_level.value if isinstance(alert_level, Enum) else alert_level,
            "description": description or f"{metric_name} {condition} {threshold}",
            "enabled": True
        }

        with self.lock:
            self.alert_rules.append(rule)

        logger.info(f"告警规则已添加: {rule_id} - {rule['description']}")
        return rule_id

    def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                self._process_metric_queue()
                self._check_systems()
                self._cleanup_metrics()

                time.sleep(1)
            except Exception as e:
                logger.error(f"监控循环错误: {str(e)}")
                time.sleep(1)

    def _process_metric_queue(self):
        """处理指标队列"""
        processed = 0
        with self.lock:
            while self.metric_queue and processed < 100:
                metric = self.metric_queue.popleft()
                metric_key = f"{metric['system_id']}_{metric['name']}"

                self.metrics[metric_key].append(metric)

                if len(self.metrics[metric_key]) > self.config["max_metrics_per_type"]:
                    self.metrics[metric_key].pop(0)

                if metric['system_id'] in self.monitored_systems:
                    self.monitored_systems[metric['system_id']]["metrics"].append(metric)
                    if len(self.monitored_systems[metric['system_id']]["metrics"]) > 100:
                        self.monitored_systems[metric['system_id']]["metrics"].pop(0)

                processed += 1

    def _check_systems(self):
        """检查被监控系统状态"""
        with self.lock:
            for system_id, system_info in self.monitored_systems.items():
                if time.time() - system_info["last_check"] > 60:
                    self._trigger_alert(
                        system_id,
                        "system_heartbeat",
                        AlertLevel.CRITICAL,
                        f"系统 {system_id} 超过60秒无心跳"
                    )

                if system_info["instance"] and hasattr(system_info["instance"], "get_status"):
                    try:
                        status = system_info["instance"].get_status()
                        self.add_metric(system_id, "status", 1 if status.get("status") == "running" else 0)
                    except Exception as e:
                        logger.error(f"检查系统 {system_id} 状态时出错: {str(e)}")

    def _cleanup_metrics(self):
        """清理过期指标"""
        current_time = time.time()
        with self.lock:
            for metric_key, metric_list in list(self.metrics.items()):
                self.metrics[metric_key] = [
                    metric for metric in metric_list
                    if current_time - metric["timestamp"] < self.config["metric_retention"]
                ]

    def _alert_loop(self):
        """告警循环"""
        while self.is_running:
            try:
                self._check_alerts()
                time.sleep(self.config["alert_check_interval"])
            except Exception as e:
                logger.error(f"告警循环错误: {str(e)}")
                time.sleep(self.config["alert_check_interval"])

    def _check_alerts(self):
        """检查告警"""
        with self.lock:
            for rule in self.alert_rules:
                if not rule["enabled"]:
                    continue

                for metric_key, metric_list in self.metrics.items():
                    if rule["metric_name"] in metric_key and metric_list:
                        latest_metric = metric_list[-1]
                        if self._evaluate_condition(latest_metric["value"], rule["condition"], rule["threshold"]):
                            self._trigger_alert(
                                latest_metric["system_id"],
                                latest_metric["name"],
                                AlertLevel(rule["level"]),
                                rule["description"],
                                latest_metric
                            )

    def _evaluate_condition(self, value, condition, threshold):
        """评估条件"""
        try:
            if condition == ">":
                return value > threshold
            elif condition == "<":
                return value < threshold
            elif condition == "==":
                return value == threshold
            elif condition == ">=":
                return value >= threshold
            elif condition == "<=":
                return value <= threshold
            return False
        except Exception as e:
            logger.error(f"评估条件错误: {str(e)}")
            return False

    def _trigger_alert(self, system_id, metric_name, level, description, metric=None):
        """触发告警"""
        alert = {
            "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
            "timestamp": time.time(),
            "system_id": system_id,
            "metric_name": metric_name,
            "level": level.value if isinstance(level, Enum) else level,
            "description": description,
            "status": "active",
            "metric": metric
        }

        with self.lock:
            self.alerts.append(alert)

            if len(self.alerts) > self.config["max_alerts"]:
                self.alerts.pop(0)

        logger.warning(f"告警触发: [{level.value}] {system_id} - {description}")

    def resolve_alert(self, alert_id):
        """解决告警"""
        with self.lock:
            for alert in self.alerts:
                if alert["alert_id"] == alert_id:
                    alert["status"] = "resolved"
                    alert["resolved_at"] = time.time()
                    return True
            return False

    def get_metrics(self, system_id=None, metric_name=None, since=None):
        """获取指标"""
        result = []
        with self.lock:
            for metric_key, metric_list in self.metrics.items():
                if system_id and system_id not in metric_key:
                    continue
                if metric_name and metric_name not in metric_key:
                    continue

                for metric in metric_list:
                    if since and metric["timestamp"] < since:
                        continue
                    result.append(metric)
        return result

    def get_alerts(self, level=None, status=None):
        """获取告警"""
        with self.lock:
            result = self.alerts.copy()

        if level:
            result = [alert for alert in result if alert["level"] == level]
        if status:
            result = [alert for alert in result if alert["status"] == status]

        return result

    def get_system_status(self):
        """获取监控系统状态"""
        try:
            return {
                "system_id": self.system_id,
                "is_running": self.is_running,
                "monitored_systems_count": len(self.monitored_systems),
                "metrics_count": sum(len(v) for v in self.metrics.values()),
                "active_alerts_count": len([a for a in self.alerts if a["status"] == "active"]),
                "alert_rules_count": len(self.alert_rules),
                "queue_size": len(self.metric_queue),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {}

    def get_dashboard_data(self):
        """获取仪表盘数据"""
        with self.lock:
            system_status = {}
            for system_id, system_info in self.monitored_systems.items():
                system_status[system_id] = {
                    "type": system_info["type"],
                    "status": system_info["status"],
                    "last_check": system_info["last_check"]
                }

            latest_metrics = {}
            for metric_key, metric_list in self.metrics.items():
                if metric_list:
                    latest_metrics[metric_key] = metric_list[-1]

            active_alerts = [alert for alert in self.alerts if alert["status"] == "active"]

            return {
                "system_status": system_status,
                "latest_metrics": latest_metrics,
                "active_alerts": active_alerts,
                "timestamp": time.time()
            }

    def generate_report(self, duration=3600):
        """生成监控报告"""
        since = time.time() - duration
        metrics = self.get_metrics(since=since)
        alerts = self.get_alerts(status="active")

        metrics_by_system = defaultdict(list)
        metrics_by_type = defaultdict(list)
        alerts_by_level = defaultdict(int)
        alerts_by_system = defaultdict(list)

        for metric in metrics:
            metrics_by_system[metric["system_id"]].append(metric)
            metrics_by_type[metric["name"]].append(metric)

        for alert in alerts:
            alerts_by_level[alert["level"]] += 1
            alerts_by_system[alert["system_id"]].append(alert)

        report = {
            "report_id": f"report_{uuid.uuid4().hex[:8]}",
            "generated_at": time.time(),
            "duration": duration,
            "metrics_summary": {
                "total_metrics": len(metrics),
                "metrics_by_system": {k: len(v) for k, v in metrics_by_system.items()},
                "metrics_by_type": {k: len(v) for k, v in metrics_by_type.items()}
            },
            "alerts_summary": {
                "total_alerts": len(alerts),
                "alerts_by_level": dict(alerts_by_level),
                "alerts_by_system": {k: len(v) for k, v in alerts_by_system.items()}
            },
            "active_alerts": alerts[:10],
            "latest_metrics": {k: v[-1] for k, v in metrics_by_type.items() if v}
        }

        report_file = f"monitoring_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"监控报告已生成: {report_file}")
        return report

class TestMonitoredSystem:
    """测试用的被监控系统"""

    def __init__(self, system_id):
        self.system_id = system_id
        self.status = "running"
        self.counter = 0

    def get_status(self):
        self.counter += 1
        return {
            "system_id": self.system_id,
            "status": self.status,
            "counter": self.counter,
            "timestamp": time.time()
        }

    def set_status(self, status):
        """设置系统状态"""
        self.status = status

def test_monitoring_system():
    """测试监控系统"""
    print("=" * 60)
    print("监控系统测试")
    print("=" * 60)

    monitoring_system = MonitoringSystem("test_monitor")

    monitoring_system.start()

    test_system1 = TestMonitoredSystem("system_1")
    test_system2 = TestMonitoredSystem("system_2")

    print("\n注册被监控系统...")
    monitoring_system.register_system("system_1", "test", test_system1)
    monitoring_system.register_system("system_2", "test", test_system2)

    print("\n添加告警规则...")
    monitoring_system.add_alert_rule(
        "rule_1",
        "system_status",
        "==",
        0,
        AlertLevel.CRITICAL,
        "系统状态异常"
    )

    print("\n模拟指标数据...")
    for i in range(10):
        monitoring_system.add_metric("system_1", "cpu_usage", 45.5 + i, MetricType.GAUGE, {"type": "test"})
        monitoring_system.add_metric("system_1", "memory_usage", 60.2 + i, MetricType.GAUGE, {"type": "test"})
        monitoring_system.add_metric("system_1", "request_count", 1000 + i * 100, MetricType.COUNTER, {"type": "test"})

        monitoring_system.add_metric("system_2", "cpu_usage", 35.8 + i, MetricType.GAUGE, {"type": "test"})
        monitoring_system.add_metric("system_2", "memory_usage", 50.1 + i, MetricType.GAUGE, {"type": "test"})
        monitoring_system.add_metric("system_2", "request_count", 800 + i * 80, MetricType.COUNTER, {"type": "test"})

        time.sleep(0.5)

    print("\n模拟系统故障...")
    monitoring_system.add_metric("system_1", "system_status", 0, MetricType.GAUGE)

    print("\n等待告警触发 (15秒)...")
    time.sleep(15)

    status = monitoring_system.get_system_status()
    print("\n监控系统状态:")
    for key, value in status.items():
        if key != "timestamp":
            print(f"  {key}: {value}")

    dashboard = monitoring_system.get_dashboard_data()
    print(f"\n仪表盘数据:")
    print(f"  系统数量: {len(dashboard['system_status'])}")
    print(f"  最新指标数量: {len(dashboard['latest_metrics'])}")
    print(f"  活跃告警数量: {len(dashboard['active_alerts'])}")

    if dashboard['active_alerts']:
        print("\n活跃告警:")
        for alert in dashboard['active_alerts']:
            print(f"  [{alert['level']}] {alert['system_id']} - {alert['description']}")

    print("\n生成监控报告...")
    report = monitoring_system.generate_report(300)
    print(f"  报告ID: {report['report_id']}")
    print(f"  指标数量: {report['metrics_summary']['total_metrics']}")

    monitoring_system.stop()

    print("\n" + "=" * 60)
    print("监控系统测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_monitoring_system()
